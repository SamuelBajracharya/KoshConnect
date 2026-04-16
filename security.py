from datetime import datetime, timedelta, timezone
from typing import Optional, Iterable, List
import hashlib
import hmac
import json
import os
import uuid

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

import models
import schemas
from database import get_db
from config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from encryption_service import encrypt, decrypt, stable_hash, mask_account_number

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="token",
    scopes={
        "account:read": "Read account profile and balances",
        "transaction:read": "Read transaction history",
        "transaction:write": "Create or simulate outgoing transactions",
        "stock:read": "Read investment instruments and holdings",
    },
)


def build_scope_claim(scopes: Optional[Iterable[str]]) -> str:
    if not scopes:
        return ""
    unique = sorted(set(scope.strip() for scope in scopes if scope and scope.strip()))
    return " ".join(unique)


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def create_access_token(
    user_id: str,
    expires_delta: Optional[timedelta] = None,
    roles: Optional[List[str]] = None,
    scopes: Optional[List[str]] = None,
):
    to_encode = {
        "sub": user_id,
        "roles": roles or ["customer"],
    }
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode.update({"exp": expire})
    to_encode.update({"scope": build_scope_claim(scopes)})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(
    security_scopes: SecurityScopes,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    if security_scopes.scopes:
        authenticate_value = f'Bearer scope="{security_scopes.scope_str}"'
    else:
        authenticate_value = "Bearer"

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": authenticate_value},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        subject: str = payload.get("sub")
        if subject is None:
            raise credentials_exception

        token_scope_str = payload.get("scope", "")
        token_scopes = token_scope_str.split()
        for required_scope in security_scopes.scopes:
            if required_scope not in token_scopes:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not enough permissions",
                    headers={"WWW-Authenticate": authenticate_value},
                )

        token_data = schemas.TokenData(user_id=subject, roles=payload.get("roles", []))
    except JWTError:
        raise credentials_exception

    user = None
    if token_data.user_id:
        try:
            parsed_id = uuid.UUID(token_data.user_id)
            user = (
                db.query(models.User).filter(models.User.user_id == parsed_id).first()
            )
        except ValueError:
            # Backward compatibility with legacy tokens where sub used phone number.
            phone_hash = stable_hash(token_data.user_id)
            user = (
                db.query(models.User)
                .filter(
                    (models.User.phonenumber_hash == phone_hash)
                    | (models.User.phonenumber == token_data.user_id)
                )
                .first()
            )

    if user is None:
        raise credentials_exception
    return user


def require_roles(required_roles: List[str]):
    async def _role_checker(current_user: models.User = Depends(get_current_user)):
        # Sandbox default: if role field is unavailable, treat user as customer.
        role = getattr(current_user, "role", "customer")
        if role not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient role permissions",
            )
        return current_user

    return _role_checker


def verify_request_signature(
    raw_body: bytes,
    request_id: str,
    signature: str,
    secret: Optional[str] = None,
) -> None:
    signing_secret = secret or os.getenv("BANK_SIGNING_SECRET") or SECRET_KEY
    message = request_id.encode("utf-8") + b"." + raw_body
    expected = hmac.new(
        signing_secret.encode("utf-8"), message, hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(expected, signature):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid X-Bank-Signature",
        )


async def require_signed_request(request: Request) -> None:
    request_id = request.headers.get("X-Request-ID")
    signature = request.headers.get("X-Bank-Signature")

    if not request_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing X-Request-ID header",
        )
    if not signature:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing X-Bank-Signature header",
        )

    raw_body = await request.body()
    verify_request_signature(
        raw_body=raw_body, request_id=request_id, signature=signature
    )


def hash_idempotency_payload(payload: dict) -> str:
    canonical_payload = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical_payload.encode("utf-8")).hexdigest()

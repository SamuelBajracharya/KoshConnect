from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from config import ACCESS_TOKEN_EXPIRE_MINUTES
from database import get_db
import models
import schemas
from security import (
    create_access_token,
    stable_hash,
    verify_password,
)

router = APIRouter(tags=["Auth"])


@router.post("/token", response_model=schemas.LoginResponse)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    phone_hash = stable_hash(form_data.username)
    user = (
        db.query(models.User)
        .filter(
            (models.User.phonenumber_hash == phone_hash)
            | (models.User.phonenumber == form_data.username)
        )
        .first()
    )
    if not user:
        raise HTTPException(status_code=404, detail="Phone number not found")

    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=401,
            detail="Incorrect password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    role = user.role if getattr(user, "role", None) else "customer"
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        user_id=str(user.user_id),
        roles=[role],
        scopes=["account:read", "transaction:read", "transaction:write", "stock:read"],
        expires_delta=access_token_expires,
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "accounts": user.accounts,
    }

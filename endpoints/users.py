from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, Security
from sqlalchemy.orm import Session

from database import get_db
from encryption_service import encrypt
import models
import schemas
from security import (
    get_current_user,
    get_password_hash,
    require_signed_request,
    stable_hash,
)
from services.common import build_user_response

router = APIRouter(tags=["Users"])


@router.post("/users/", response_model=schemas.User)
def create_user(
    user: schemas.UserCreate,
    request: Request,
    _: None = Depends(require_signed_request),
    db: Session = Depends(get_db),
):
    phone_hash = stable_hash(user.phonenumber)
    db_user = (
        db.query(models.User)
        .filter(
            (models.User.phonenumber_hash == phone_hash)
            | (models.User.phonenumber == user.phonenumber)
        )
        .first()
    )
    if db_user:
        raise HTTPException(status_code=400, detail="Phone number already registered")

    email_hash = stable_hash(user.email) if user.email else None
    if (
        email_hash
        and db.query(models.User).filter(models.User.email_hash == email_hash).first()
    ):
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = get_password_hash(user.password)
    user_id = uuid4()
    db_user = models.User(
        user_id=user_id,
        username=user.username,
        phonenumber=None,
        phonenumber_encrypted=encrypt(user.phonenumber, aad=f"user_phone:{user_id}"),
        phonenumber_hash=phone_hash,
        email_encrypted=(
            encrypt(user.email, aad=f"user_email:{user_id}") if user.email else None
        ),
        email_hash=email_hash,
        full_name=user.full_name,
        hashed_password=hashed_password,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return build_user_response(db_user)


@router.get("/users/me/", response_model=schemas.User)
async def read_users_me(
    current_user: models.User = Security(get_current_user, scopes=["account:read"])
):
    return build_user_response(current_user)


@router.get("/users/{user_id}", response_model=schemas.User)
def get_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Security(get_current_user, scopes=["account:read"]),
):
    if current_user.user_id != user_id:
        raise HTTPException(
            status_code=403, detail="Not authorized to access this user"
        )
    db_user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return build_user_response(db_user)


@router.get("/users/{user_id}/accounts", response_model=list[schemas.Account])
def get_user_accounts(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Security(get_current_user, scopes=["account:read"]),
):
    if current_user.user_id != user_id:
        raise HTTPException(
            status_code=403, detail="Not authorized to access these accounts"
        )
    db_user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user.accounts

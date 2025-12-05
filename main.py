from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from datetime import timedelta
import models
import schemas
from database import get_db, engine
from security import (
    create_access_token,
    get_current_user,
    get_password_hash,
    verify_password,
)

# JWT settings
SECRET_KEY = "your-secret-key"  # Change this in production
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


# Use lifespan instead of deprecated on_event
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Creating database tables (if not exist)...")
    models.Base.metadata.create_all(bind=engine)
    print("✅ Tables ready!")
    yield  # startup done — now the app runs
    print("🛑 Shutting down app...")


app = FastAPI(title="Student Finance API", version="1.0", lifespan=lifespan)

origins = [
    "http://localhost:3000",  # local dev frontend
    "https://koshconnect.vercel.app",  # production (if deployed)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # can use ["*"] for testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================
# AUTHENTICATION ROUTES
# =========================
@app.post("/token", response_model=schemas.Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


# =========================
# USER ROUTES
# =========================
@app.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        hashed_password=hashed_password,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@app.get("/users/me/", response_model=schemas.User)
async def read_users_me(current_user: models.User = Depends(get_current_user)):
    return current_user


@app.get("/users/{user_id}", response_model=schemas.User)
def get_user(user_id: UUID, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@app.get("/users/{user_id}/accounts", response_model=List[schemas.Account])
def get_user_accounts(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if current_user.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to access these accounts")
    db_user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user.accounts


# =========================
# ACCOUNT ROUTES
# =========================
@app.get("/accounts/{account_id}", response_model=schemas.AccountWithTransactions)
def get_account(
    account_id: UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    db_account = (
        db.query(models.Account).filter(models.Account.account_id == account_id).first()
    )
    if db_account is None:
        raise HTTPException(status_code=404, detail="Account not found")
    if db_account.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized to access this account")
    return db_account


@app.get(
    "/accounts/{account_id}/transactions", response_model=List[schemas.Transaction]
)
def get_account_transactions(
    account_id: UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    db_account = (
        db.query(models.Account).filter(models.Account.account_id == account_id).first()
    )
    if db_account is None:
        raise HTTPException(status_code=404, detail="Account not found")
    if db_account.user_id != current_user.user_id:
        raise HTTPException(
            status_code=403, detail="Not authorized to access these transactions"
        )
    return db_account.transactions


# =========================
# TRANSACTION ROUTES
# =========================
@app.get("/transactions/{transaction_id}", response_model=schemas.Transaction)
def get_transaction(
    transaction_id: UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    db_transaction = (
        db.query(models.Transaction)
        .filter(models.Transaction.transaction_id == transaction_id)
        .first()
    )
    if db_transaction is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    if db_transaction.account.user_id != current_user.user_id:
        raise HTTPException(
            status_code=403, detail="Not authorized to access this transaction"
        )
    return db_transaction


@app.post("/transactions/", response_model=schemas.Transaction)
def add_transaction(
    transaction: schemas.TransactionCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    db_account = (
        db.query(models.Account)
        .filter(models.Account.account_id == transaction.account_id)
        .first()
    )
    if db_account is None:
        raise HTTPException(status_code=404, detail="Account not found")
    if db_account.user_id != current_user.user_id:
        raise HTTPException(
            status_code=403, detail="Not authorized to add transaction to this account"
        )

    db_transaction = models.Transaction(**transaction.dict())
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    return db_transaction

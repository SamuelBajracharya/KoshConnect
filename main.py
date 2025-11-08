from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware  # 👈 added
import models
import schemas
from database import get_db, engine


# Use lifespan instead of deprecated on_event
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Creating database tables (if not exist)...")
    models.Base.metadata.create_all(bind=engine)
    print("✅ Tables ready!")
    yield  # startup done — now the app runs
    print("🛑 Shutting down app...")


app = FastAPI(title="Student Finance API", version="1.0", lifespan=lifespan)

# ✅ Enable CORS for frontend (Next.js)
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
# USER ROUTES
# =========================
@app.get("/users/{user_id}", response_model=schemas.User)
def get_user(user_id: UUID, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@app.get("/users/{user_id}/accounts", response_model=List[schemas.Account])
def get_user_accounts(user_id: UUID, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user.accounts


# =========================
# ACCOUNT ROUTES
# =========================
@app.get("/accounts/{account_id}", response_model=schemas.AccountWithTransactions)
def get_account(account_id: UUID, db: Session = Depends(get_db)):
    db_account = (
        db.query(models.Account).filter(models.Account.account_id == account_id).first()
    )
    if db_account is None:
        raise HTTPException(status_code=404, detail="Account not found")
    return db_account


@app.get(
    "/accounts/{account_id}/transactions", response_model=List[schemas.Transaction]
)
def get_account_transactions(account_id: UUID, db: Session = Depends(get_db)):
    db_account = (
        db.query(models.Account).filter(models.Account.account_id == account_id).first()
    )
    if db_account is None:
        raise HTTPException(status_code=404, detail="Account not found")
    return db_account.transactions


# =========================
# TRANSACTION ROUTES
# =========================
@app.get("/transactions/{transaction_id}", response_model=schemas.Transaction)
def get_transaction(transaction_id: UUID, db: Session = Depends(get_db)):
    db_transaction = (
        db.query(models.Transaction)
        .filter(models.Transaction.transaction_id == transaction_id)
        .first()
    )
    if db_transaction is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return db_transaction


@app.post("/transactions/", response_model=schemas.Transaction)
def add_transaction(
    transaction: schemas.TransactionCreate, db: Session = Depends(get_db)
):
    db_transaction = models.Transaction(**transaction.dict())
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    return db_transaction

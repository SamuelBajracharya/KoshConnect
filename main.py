from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from datetime import timedelta
from decimal import Decimal
import models
import schemas
from database import get_db, engine, SessionLocal
from config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from security import (
    create_access_token,
    get_current_user,
    get_password_hash,
    verify_password,
)


# Approximate market snapshot for mock use (as of 2026-02-21)
MARKET_DUMMY_STOCKS = [
    {
        "symbol": "AAPL",
        "name": "Apple Inc.",
        "current_price": "228.90",
        "currency": "USD",
    },
    {
        "symbol": "MSFT",
        "name": "Microsoft Corporation",
        "current_price": "436.10",
        "currency": "USD",
    },
    {
        "symbol": "GOOGL",
        "name": "Alphabet Inc. Class A",
        "current_price": "186.75",
        "currency": "USD",
    },
    {
        "symbol": "AMZN",
        "name": "Amazon.com, Inc.",
        "current_price": "204.35",
        "currency": "USD",
    },
    {
        "symbol": "NVDA",
        "name": "NVIDIA Corporation",
        "current_price": "965.20",
        "currency": "USD",
    },
    {
        "symbol": "TSLA",
        "name": "Tesla, Inc.",
        "current_price": "242.40",
        "currency": "USD",
    },
]


def seed_stock_instruments(db: Session):
    users = db.query(models.User).all()
    if not users:
        return

    quantity_templates = ["3.500000", "7.000000", "1.250000", "4.000000"]
    buy_multipliers = ["0.87", "0.93", "1.05", "1.12"]

    for user_index, user in enumerate(users):
        user_id_str = str(user.user_id)
        existing_symbols = {
            row.symbol
            for row in db.query(models.StockInstrument.symbol)
            .filter(models.StockInstrument.user_id == user_id_str)
            .all()
        }

        # Rotate the market list so different users get different mixes
        offset = user_index % len(MARKET_DUMMY_STOCKS)
        assigned = (MARKET_DUMMY_STOCKS[offset:] + MARKET_DUMMY_STOCKS[:offset])[:4]

        for stock_index, stock in enumerate(assigned):
            if stock["symbol"] in existing_symbols:
                continue

            current_price = Decimal(stock["current_price"])
            avg_multiplier = Decimal(buy_multipliers[stock_index])
            quantity = Decimal(quantity_templates[stock_index])

            db.add(
                models.StockInstrument(
                    user_id=user_id_str,
                    symbol=stock["symbol"],
                    name=stock["name"],
                    quantity=quantity,
                    average_buy_price=(current_price * avg_multiplier),
                    current_price=current_price,
                    currency=stock["currency"],
                )
            )

    db.commit()


# Use lifespan instead of deprecated on_event
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Creating database tables (if not exist)...")
    models.Base.metadata.create_all(bind=engine)
    print("Tables ready!")

    db = SessionLocal()
    try:
        seed_stock_instruments(db)
        print("Stock instruments seeded (if missing).")
    finally:
        db.close()

    yield  # startup done — now the app runs
    print("Shutting down app...")


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


# AUTHENTICATION ROUTES
@app.post("/token", response_model=schemas.LoginResponse)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    # The `username` field from the OAuth2 form is used to accept the phone number.
    user = (
        db.query(models.User)
        .filter(models.User.phonenumber == form_data.username)
        .first()
    )
    if not user:
        raise HTTPException(
            status_code=404,
            detail="Phone number not found",
        )
    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=401,
            detail="Incorrect password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Note: The token's 'sub' claim still uses the user's actual username, not their phone number.
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.phonenumber}, expires_delta=access_token_expires
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "accounts": user.accounts,
    }


# USER ROUTES
@app.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = (
        db.query(models.User)
        .filter(models.User.phonenumber == user.phonenumber)
        .first()
    )
    if db_user:
        raise HTTPException(status_code=400, detail="Phone number already registered")
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        username=user.username,
        phonenumber=user.phonenumber,
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
        raise HTTPException(
            status_code=403, detail="Not authorized to access these accounts"
        )
    db_user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user.accounts


# ACCOUNT ROUTES
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
        raise HTTPException(
            status_code=403, detail="Not authorized to access this account"
        )
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


# TRANSACTION ROUTES
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


@app.get("/users/{user_id}/stocks", response_model=List[schemas.StockInstrument])
def get_user_stocks(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if current_user.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to access stocks")

    return (
        db.query(models.StockInstrument)
        .filter(models.StockInstrument.user_id == str(user_id))
        .order_by(models.StockInstrument.symbol.asc())
        .all()
    )


@app.post("/stocks/", response_model=schemas.StockInstrument)
def add_stock_instrument(
    stock: schemas.StockInstrumentCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if stock.user_id != str(current_user.user_id):
        raise HTTPException(
            status_code=403, detail="Not authorized to add stock for this user"
        )

    exists = (
        db.query(models.StockInstrument)
        .filter(
            models.StockInstrument.user_id == stock.user_id,
            models.StockInstrument.symbol == stock.symbol,
        )
        .first()
    )
    if exists:
        raise HTTPException(
            status_code=400, detail="Stock symbol already exists for this user"
        )

    db_stock = models.StockInstrument(**stock.dict())
    db.add(db_stock)
    db.commit()
    db.refresh(db_stock)
    return db_stock


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

from pydantic import BaseModel, Field, constr
from typing import List, Optional
from uuid import UUID
from datetime import datetime


# Token Schemas
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    phonenumber: Optional[str] = None


# Transaction Schemas
class TransactionBase(BaseModel):
    account_id: UUID
    date: datetime
    amount: float
    currency: str
    type: str
    status: str
    description: Optional[str] = None

    merchant: Optional[str] = None
    category: Optional[str] = None


class TransactionCreate(TransactionBase):
    pass


class Transaction(TransactionBase):
    transaction_id: UUID

    class Config:
        from_attributes = True


# Account Schemas
class AccountBase(BaseModel):
    user_id: UUID
    bank_name: str
    account_number_masked: str
    account_type: str
    balance: float


class AccountCreate(AccountBase):
    pass


class Account(AccountBase):
    account_id: UUID

    class Config:
        from_attributes = True


class AccountWithTransactions(Account):
    transactions: List[Transaction] = Field(default_factory=list)

    class Config:
        from_attributes = True


# User Schemas
class UserBase(BaseModel):
    username: str
    phonenumber: str
    full_name: str


class UserCreate(UserBase):
    # bcrypt supports only up to 72 bytes
    password: constr(max_length=72)


class User(UserBase):
    user_id: UUID
    created_at: datetime
    accounts: List[Account] = Field(default_factory=list)

    class Config:
        from_attributes = True


# =========================
# Login Response Schemas
# =========================
class LoginResponse(Token):
    accounts: List[Account] = Field(default_factory=list)

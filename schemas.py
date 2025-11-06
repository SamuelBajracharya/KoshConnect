from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID
from datetime import datetime


# =========================
# Transaction Schemas
# =========================
class TransactionBase(BaseModel):
    account_id: UUID
    date: datetime
    amount: float
    currency: str
    type: str
    status: str
    description: Optional[str] = None


class TransactionCreate(TransactionBase):
    pass


class Transaction(TransactionBase):
    transaction_id: UUID

    class Config:
        from_attributes = True


# =========================
# Account Schemas
# =========================
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
    transactions: List[Transaction] = []

    class Config:
        from_attributes = True


# =========================
# User Schemas
# =========================
class UserBase(BaseModel):
    email: str
    full_name: str


class UserCreate(UserBase):
    pass


class User(UserBase):
    user_id: UUID
    created_at: datetime
    accounts: List[Account] = []

    class Config:
        from_attributes = True

from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime


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
    is_new: bool = False

    class Config:
        from_attributes = True

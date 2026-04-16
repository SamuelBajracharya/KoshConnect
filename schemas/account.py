from pydantic import BaseModel, Field
from typing import List
from uuid import UUID

from schemas.transaction import Transaction


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

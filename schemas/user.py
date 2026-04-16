from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from schemas.account import Account


class UserBase(BaseModel):
    username: str
    phonenumber: str
    email: Optional[str] = None
    full_name: str


class UserCreate(UserBase):
    password: str = Field(max_length=72)


class User(UserBase):
    user_id: UUID
    phonenumber: Optional[str] = None
    created_at: datetime
    accounts: List[Account] = Field(default_factory=list)

    class Config:
        from_attributes = True

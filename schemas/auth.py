from pydantic import BaseModel, Field
from typing import Optional, List
from schemas.account import Account


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    user_id: Optional[str] = None
    roles: List[str] = Field(default_factory=list)


class LoginResponse(Token):
    accounts: List[Account] = Field(default_factory=list)

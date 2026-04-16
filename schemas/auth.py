from pydantic import BaseModel, Field
from typing import Optional, List


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    user_id: Optional[str] = None
    roles: List[str] = Field(default_factory=list)


class LoginResponse(Token):
    accounts: list = Field(default_factory=list)

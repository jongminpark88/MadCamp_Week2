from pydantic import BaseModel
from typing import Optional

class AccessTokenRequest(BaseModel):
    accessToken: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class User(BaseModel):
    username: str

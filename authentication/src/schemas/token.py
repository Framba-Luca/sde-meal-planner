from pydantic import BaseModel
from typing import Optional
from src.schemas.user import User

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    user: User

class TokenPayload(BaseModel):
    sub: Optional[str] = None
    type: Optional[str] = None  # Can be ---> "access" or "refresh"
    full_name: Optional[str] = None
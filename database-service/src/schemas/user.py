from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None

class UserCreate(UserBase):
    hashed_password: str

class UserResponse(UserBase):
    id: int
    created_at: str | datetime
    hashed_password: str

    class Config:
        from_attributes = True
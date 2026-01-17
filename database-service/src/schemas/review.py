from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ReviewCreate(BaseModel):
    user_id: int
    recipe_id: int
    rating: int
    comment: str

class ReviewResponse(BaseModel):
    id: int
    user_id: int
    recipe_id: int
    rating: int
    comment: str
    created_at: datetime
    username: Optional[str] = None

    class Config:
        from_attributes = True
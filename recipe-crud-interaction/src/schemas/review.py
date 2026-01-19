from pydantic import BaseModel, Field
from typing import Optional

class ReviewCreate(BaseModel):
    recipe_id: Optional[int] = None
    external_id: Optional[str] = None
    rating: int = Field(..., ge=1, le=5)
    comment: str

class ReviewResponse(BaseModel):
    id: int
    recipe_id: int
    user_id: int
    rating: int
    comment: str
    created_at: str
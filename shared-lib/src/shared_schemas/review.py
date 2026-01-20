from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime

# --- BASE ---
class ReviewBase(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    comment: str

# --- INPUTS ---
class ReviewCreate(ReviewBase):
    recipe_id: Optional[int] = None
    external_id: Optional[str] = None

class ReviewCreateDB(ReviewBase):
    user_id: int
    recipe_id: int

# --- OUTPUTS ---
class ReviewResponse(ReviewBase):
    id: int
    user_id: int
    recipe_id: int
    created_at: datetime
    username: Optional[str] = None 

    model_config = ConfigDict(from_attributes=True)
from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field

class Review(SQLModel, table=True):
    __tablename__ = "reviews"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    recipe_id: int = Field(foreign_key="recipes.id")
    
    rating: int
    comment: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
from typing import Optional, List
from datetime import datetime
from sqlmodel import Field, SQLModel, Relationship

class User(SQLModel, table=True):
    __tablename__ = "users"

    # Primary Key
    id: Optional[int] = Field(default=None, primary_key=True)

    # Required and indexed fields
    username: str = Field(index=True, unique=True, max_length=50)
    hashed_password: str  # The stored password is already hashed

    # Optional fields
    email: Optional[str] = Field(default=None, max_length=100)
    full_name: Optional[str] = Field(default=None, max_length=100)

    # System fields (with default values)
    created_at: datetime = Field(default_factory=datetime.now)
    is_active: bool = Field(default=True)  # Useful to "ban" users without deleting them

    # Relationships (optional: uncomment if you want to navigate user.recipes)
    # recipes: List["Recipe"] = Relationship(back_populates="user")
    # meal_plans: List["MealPlan"] = Relationship(back_populates="user")
    # reviews: List["Review"] = Relationship(back_populates="user")

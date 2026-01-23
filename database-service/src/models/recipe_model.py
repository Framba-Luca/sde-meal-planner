from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship

# Ingredients table (child of Recipe)
class RecipeIngredient(SQLModel, table=True):
    __tablename__ = "recipe_ingredients"

    id: Optional[int] = Field(default=None, primary_key=True)
    recipe_id: Optional[int] = Field(default=None, foreign_key="recipes.id")
    ingredient_name: str
    measure: Optional[str] = None

    # Inverse relationship (optional but useful)
    recipe: Optional["Recipe"] = Relationship(back_populates="ingredients")


# Recipes table
class Recipe(SQLModel, table=True):
    __tablename__ = "recipes"  # Replaces the old 'custom_recipes'

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(
        default=None,
        foreign_key="users.id"
    )  # Null if this is a system or pure shadow recipe

    # Basic data
    name: str
    category: Optional[str] = None
    area: Optional[str] = None
    instructions: Optional[str] = None
    image: Optional[str] = None
    tags: Optional[str] = None

    # Shadow / Custom logic
    is_custom: bool = Field(default=True)
    external_id: Optional[str] = Field(
        default=None,
        index=True,
        unique=True
    )  # TheMealDB ID

    # Relationships
    ingredients: List[RecipeIngredient] = Relationship(
        back_populates="recipe",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    # reviews: List["Review"] = Relationship(...)
    # Will be added after creating the Review model

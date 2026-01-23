from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime

# --- INGREDIENT SCHEMAS ---

class IngredientCreate(BaseModel):
    name: str
    measure: Optional[str] = None


class IngredientResponse(BaseModel):
    name: str = Field(validation_alias="ingredient_name")
    measure: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# --- RECIPE SCHEMAS (CUSTOM / INTERNAL) ---

class CustomRecipeCreate(BaseModel):
    user_id: int
    name: str
    category: Optional[str] = None
    area: Optional[str] = None
    instructions: Optional[str] = None
    image: Optional[str] = None
    tags: Optional[str] = None

    ingredients: List[IngredientCreate] = Field(default_factory=list)


class CustomRecipeResponse(BaseModel):
    id: int
    user_id: int
    name: str
    category: Optional[str] = None
    area: Optional[str] = None
    instructions: Optional[str] = None
    image: Optional[str] = None
    tags: Optional[str] = None
    is_custom: bool
    created_at: Optional[datetime] = None

    ingredients: List[IngredientResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class ShadowRecipeCreate(BaseModel):
    external_id: str
    name: str
    image: Optional[str] = None
    category: Optional[str] = None
    area: Optional[str] = None

class RecipeUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    area: Optional[str] = None
    instructions: Optional[str] = None
    image: Optional[str] = None
    tags: Optional[str] = None
    
    ingredients: Optional[List[IngredientCreate]] = None

class RecipeUnifiedResponse(BaseModel):
    """
    Schema used for the search/detail endpoint that handles both
    Internal (Custom) and External (TheMealDB) recipes.
    """
    id: Optional[int] = None
    external_id: Optional[str] = None
    name: str
    
    category: Optional[str] = None
    area: Optional[str] = None
    instructions: Optional[str] = None
    image: Optional[str] = None
    tags: Optional[str] = None
    
    user_id: Optional[int] = None       
    is_custom: bool = False
    source: str = "external"
    
    ingredients: List[Dict[str, Any]] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


RecipeCreate = CustomRecipeCreate
RecipeResponse = CustomRecipeResponse
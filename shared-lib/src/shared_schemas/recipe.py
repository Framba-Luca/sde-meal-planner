from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime

# --- INGREDIENTS ---
class IngredientBase(BaseModel):
    name: str
    measure: Optional[str] = None

class IngredientCreate(IngredientBase):
    pass

class IngredientResponse(IngredientBase):
    name: str = Field(validation_alias="ingredient_name", default=None)
    
    model_config = ConfigDict(from_attributes=True)

# --- RECIPE BASE ---
class RecipeBase(BaseModel):
    name: str
    category: Optional[str] = None
    area: Optional[str] = None
    instructions: Optional[str] = None
    image: Optional[str] = None
    tags: Optional[str] = None

# --- RECIPE INPUTS ---
class CustomRecipeCreate(RecipeBase):
    user_id: int
    ingredients: List[IngredientCreate] = Field(default_factory=list)

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

# --- RECIPE OUTPUTS ---
class CustomRecipeResponse(RecipeBase):
    id: int
    user_id: int
    is_custom: bool
    created_at: Optional[datetime] = None
    external_id: Optional[str] = None
    
    ingredients: List[IngredientResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)

class RecipeUnifiedResponse(RecipeBase):
    id: Optional[int] = None
    external_id: Optional[str] = None
    is_custom: bool
    source: str = "internal"
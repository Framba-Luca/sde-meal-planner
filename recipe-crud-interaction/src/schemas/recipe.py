from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class RecipeBase(BaseModel):
    name: str
    description: Optional[str] = None
    instructions: Optional[str] = None
    image: Optional[str] = ""
    category: Optional[str] = None
    area: Optional[str] = None
    ingredients: Optional[List[Dict[str, Any]]] = []

class RecipeCreate(RecipeBase):
    user_id: int 

class RecipeUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    instructions: Optional[str] = None
    image: Optional[str] = None

class RecipeResponse(RecipeBase):
    id: int
    user_id: int
    external_id: Optional[str] = None
    is_custom: bool = True

    class Config:
        from_attributes = True
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class CustomRecipeCreate(BaseModel):
    user_id: int
    name: str
    category: Optional[str] = None
    area: Optional[str] = None
    instructions: Optional[str] = None
    image: Optional[str] = None
    tags: Optional[str] = None
    ingredients: List[Dict[str, Any]] = []

class CustomRecipeResponse(CustomRecipeCreate):
    id: int
    created_at: str | Any
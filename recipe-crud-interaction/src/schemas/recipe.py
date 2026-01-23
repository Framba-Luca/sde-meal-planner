from pydantic import BaseModel
from typing import Optional, List, Dict, Any

# -------------------------------------------------
# CORE FIELDS
# -------------------------------------------------

class RecipeCore(BaseModel):
    name: str
    image: Optional[str] = None
    category: Optional[str] = None
    area: Optional[str] = None
    
# -------------------------------------------------
# INPUT SCHEMAS (Create/Update)
# -------------------------------------------------

class RecipeCreate(RecipeCore):
    user_id: int
    instructions: Optional[str] = None
    ingredients: List[Dict[str, Any]] = []

class RecipeUpdate(RecipeCore):
    name: Optional[str] = None
    instructions: Optional[str] = None
    image: Optional[str] = None
    category: Optional[str] = None
    area: Optional[str] = None
    ingredients: Optional[List[Dict[str, Any]]] = None

# -------------------------------------------------
# OUTPUT SCHEMAS (Internal DB)
# -------------------------------------------------

class RecipeResponse(RecipeCore):
    id: int
    user_id: int
    external_id: Optional[str] = None
    instructions: Optional[str] = None
    is_custom: bool = True
    ingredients: List[Dict[str, Any]] = []

    class Config:
        from_attributes = True

# -------------------------------------------------
# UNIFIED RESPONSES (Search vs Detail)
# -------------------------------------------------

class RecipeUnifiedSummary(RecipeCore):
    id: Optional[int] = None
    external_id: Optional[str] = None
    is_custom: bool
    source: str = "external"
    class Config:
        from_attributes = True

class RecipeUnifiedDetail(RecipeUnifiedSummary):
    instructions: Optional[str] = None
    ingredients: List[Dict[str, Any]] = []
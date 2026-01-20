from pydantic import BaseModel
from typing import Optional, List, Dict, Any

# -------------------------------------------------
# CORE FIELDS (shared across all recipe schemas)
# -------------------------------------------------

class RecipeCore(BaseModel):
    name: str
    instructions: Optional[str] = None
    image: Optional[str] = None
    category: Optional[str] = None
    area: Optional[str] = None


# -------------------------------------------------
# INPUT SCHEMAS
# -------------------------------------------------

class RecipeCreate(RecipeCore):
    user_id: int
    ingredients: List[Dict[str, Any]] = []


class RecipeUpdate(RecipeCore):
    name: Optional[str] = None
    instructions: Optional[str] = None
    image: Optional[str] = None
    category: Optional[str] = None
    area: Optional[str] = None


# -------------------------------------------------
# OUTPUT SCHEMAS (DB)
# -------------------------------------------------

class RecipeResponse(RecipeCore):
    id: int
    user_id: int
    external_id: Optional[str] = None
    is_custom: bool = True

    class Config:
        from_attributes = True


# -------------------------------------------------
# UNIFIED SEARCH RESPONSE (internal + external)
# -------------------------------------------------

class RecipeUnifiedResponse(RecipeCore):
    id: Optional[int] = None
    external_id: Optional[str] = None
    is_custom: bool
    source: str = "internal"

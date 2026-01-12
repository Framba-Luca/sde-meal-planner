from pydantic import BaseModel
from typing import Optional, Dict, Any

class TokenRevokeRequest(BaseModel):
    token: str
    ttl: int

class TokenCheckResponse(BaseModel):
    is_valid: bool
    user_data: Optional[Dict[str, Any]] = None
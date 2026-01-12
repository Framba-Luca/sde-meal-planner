from fastapi import APIRouter, HTTPException, status
from src.schemas.token import TokenRevokeRequest, TokenCheckResponse
from src.core.config import settings
from jose import jwt, JWTError
import redis

router = APIRouter()

# Client Redis interno (per questo endpoint specifico)
try:
    redis_client = redis.Redis(
        host=settings.REDIS_HOST, 
        port=settings.REDIS_PORT, 
        db=settings.REDIS_DB, 
        decode_responses=True
    )
except:
    redis_client = None

@router.post("/revoke", status_code=status.HTTP_200_OK)
async def revoke_token(request: TokenRevokeRequest):
    """
    Revoke a token (Logout).
    Called by Auth Service. Writes to Redis Blacklist.
    """
    if not redis_client:
         raise HTTPException(status_code=503, detail="Redis unavailable")

    try:
        redis_client.setex(
            name=f"blacklist:{request.token}",
            time=request.ttl,
            value="revoked"
        )
        return {"message": "Token revoked"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))

@router.get("/verify", response_model=TokenCheckResponse)
async def verify_token_status(token: str):
    """
    Check if token is valid and not blacklisted.
    """
    # 1. Check Redis
    if redis_client:
        is_blacklisted = redis_client.get(f"blacklist:{token}")
        if is_blacklisted:
            return {"is_valid": False}
    
    # 2. Check Signature
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return {"is_valid": True, "user_data": payload}
    except JWTError:
        return {"is_valid": False}
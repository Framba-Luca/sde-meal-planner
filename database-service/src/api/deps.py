from typing import Annotated, Optional, Dict, Any
from fastapi import Header, HTTPException, status, Depends
from jose import jwt, JWTError
import redis

from src.core.config import settings
from src.schemas.token import TokenCheckResponse

# Initialize Redis Client
try:
    redis_client = redis.Redis(
        host=settings.REDIS_HOST, 
        port=settings.REDIS_PORT, 
        db=settings.REDIS_DB, 
        decode_responses=True
    )
except Exception as e:
    print(f"Redis Connection Warning: {e}")
    redis_client = None

async def verify_token(authorization: Annotated[str, Header()] = None) -> Dict[str, Any]:
    """
    Dependency to protect the routes.
    1. Check Headers
    2. Checks Redis Blacklist
    3. Checks JWT Signature
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization Header"
        )
    
    try:
        scheme, token = authorization.split()
        if scheme.lower() != 'bearer':
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Auth Scheme"
            )
            
        # 1. Check Redis Blacklist
        if redis_client:
            is_blacklisted = redis_client.get(f"blacklist:{token}")
            if is_blacklisted:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token revoked"
                )
        
        # 2. Check JWT Signature
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload

    except (ValueError, JWTError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
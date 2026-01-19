from typing import Generator, Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import ValidationError

from src.core.config import settings
from src.schemas.token import TokenPayload
from src.schemas.user import User
from src.services.auth_service import AuthService
from src.services.oauth_service import GoogleAuthService
from src.infrastructure.user_client import UserRemoteRepository
from src.infrastructure.cache import RedisClient, redis_client

# This expects the header "Authorization: Bearer <token>"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# --- Infrastructure Dependencies ---

async def get_redis_client() -> RedisClient:
    """
    Returns the singleton instance of RedisClient.
    """
    return redis_client

def get_user_repo() -> UserRemoteRepository:
    """
    Returns the HTTP Client for the Database Service.
    """
    return UserRemoteRepository()

# --- Service Dependencies ---

def get_auth_service(
    user_repo: UserRemoteRepository = Depends(get_user_repo)
) -> AuthService:
    """
    Injects the User Repo into the Auth Service.
    """
    return AuthService(user_repo=user_repo)

def get_google_service(
    user_repo: UserRemoteRepository = Depends(get_user_repo)
) -> GoogleAuthService:
    """
    Injects the User Repo into the Google Auth Service.
    """
    return GoogleAuthService(user_repo=user_repo)

# --- Current User Logic (Token Validation) ---

async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    redis: RedisClient = Depends(get_redis_client),
    user_repo: UserRemoteRepository = Depends(get_user_repo)
) -> User:
    """
    1. Decodes the JWT.
    2. Checks if the token is in the Redis Blacklist (Revoked).
    3. Retrieves user data (optional: can be skipped if claims are enough).
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # A. Check Blacklist (Logout / Revocation)
    if await redis.is_token_revoked(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked (logged out)"
        )

    # B. Decode Token
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        
        # We can map other claims here if needed
        token_data = TokenPayload(**payload)
        
    except (JWTError, ValidationError):
        raise credentials_exception

    # C. (Optional) Validate that the user still exists in the DB
    # If performance is key, you can skip this and trust the token until expiry.
    # However, checking ensures banned/deleted users are blocked immediately.
    user_data = await user_repo.get_user_by_username(username)
    if user_data is None:
        raise credentials_exception
        
    return User(**user_data)
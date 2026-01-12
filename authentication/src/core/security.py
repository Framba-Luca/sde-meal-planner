from datetime import datetime, timedelta
from typing import Any, Union
from jose import jwt
from passlib.context import CryptContext
from src.core.config import settings

# Hashing configuration (Bcrypt is a robust standard)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies if the password equals to the saved hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Generate the hashing of password."""
    return pwd_context.hash(password)

def create_token(subject: Union[str, Any], token_type: str, expires_delta: timedelta = None) -> str:
    """
    Create a JWT Token.
    :param subject: usually username (the 'sub' claim standard)
    :param token_type: "access" or "refresh"
    :param expires_delta: custom expiration time
    """
    expire = datetime.now() + expires_delta
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "type": token_type
    }

    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def create_access_token(subject: Union[str, Any]) -> str:
    """
    Create the access JWT Token.
    """
    return create_token(
        subject, 
        "access", 
        timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

def create_refresh_token(subject: Union[str, Any]) -> str:
    """
    Create the refresh JWT Token.
    """
    return create_token(
        subject, 
        "refresh", 
        timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )
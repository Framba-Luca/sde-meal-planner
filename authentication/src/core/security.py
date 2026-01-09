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

def create_access_token(subject: Union[str, Any], extra_claims: dict = None) -> str:
    """
    Create a JWT Token.
    :param subject: usually username (the 'sub' claim standard)
    :param extra_claims: Extra data (es. full_name, role)
    """
    if extra_claims is None:
        extra_claims = {}
        
    expire = datetime.now() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Construct the payload
    to_encode = extra_claims.copy()
    to_encode.update({"exp": expire, "sub": str(subject)})
    
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError

from src.core.config import settings
from src.core import security
from src.schemas.user import User
from src.infrastructure.user_client import UserRemoteRepository
from src.services.auth_service import AuthService
from src.services.oauth_service import GoogleAuthService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

# 1. Dependency for Client (Singleton-ish)
def get_user_repo() -> UserRemoteRepository:
    return UserRemoteRepository()

# 2. Dependency for Service
def get_auth_service(repo: UserRemoteRepository = Depends(get_user_repo)) -> AuthService:
    return AuthService(repo)

def get_google_service(repo: UserRemoteRepository = Depends(get_user_repo)) -> GoogleAuthService:
    return GoogleAuthService(repo)

# 3. Dependency for protecting routes (Auth Middleware)
async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        full_name: str = payload.get("full_name")
        if username is None:
            raise credentials_exception
        
        # Qui potremmo chiamare il DB per assicurarci che l'utente esista ancora,
        # ma per performance ci fidiamo del token (Stateless Auth)
        # Da vedere più avanti se serve un controllo extra
        return User(username=username, full_name=full_name)
        
    except JWTError:
        raise credentials_exception
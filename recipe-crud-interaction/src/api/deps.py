from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from src.services.recipe_service import RecipeService
from src.services.review_service import ReviewService
from src.services.auth_client import AuthClient
from src.core.config import settings

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.AUTHENTICATION_SERVICE_URL}{settings.API_V1_STR}/auth/login"
)

def get_recipe_service() -> RecipeService:
    return RecipeService()

def get_review_service() -> ReviewService:
    return ReviewService()

def get_auth_client() -> AuthClient:
    return AuthClient()

def get_current_user(
    token: str = Depends(oauth2_scheme),
    auth_client: AuthClient = Depends(get_auth_client)
) -> int:
    return auth_client.get_user_id_from_token(token)
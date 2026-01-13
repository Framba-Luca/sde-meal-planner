from fastapi import APIRouter, Depends, Header, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import RedirectResponse
from urllib.parse import urlencode
from typing import Annotated
import traceback
import sys

from src.services.auth_service import AuthService
from src.services.oauth_service import GoogleAuthService
from src.schemas.token import Token
from src.schemas.user import UserCreate, User
from src.api import deps
from src.core.config import settings

router = APIRouter()

# --- Classic Auth ---

@router.post("/login", response_model=Token)
async def login_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    service: AuthService = Depends(deps.get_auth_service)
):
    """
    Login endpoint accepting JSON body.
    """
    return await service.authenticate_user(form_data.username, form_data.password)

@router.post("/refresh", response_model=Token)
async def refresh_access_token(
    refresh_token: Annotated[str, Header(alias="X-Refresh-Token")],
    service: AuthService = Depends(deps.get_auth_service)
):
    """
    Refresh access token using a valid refresh token.
    The refresh token must be provided in the 'X-Refresh-Token' header.
    """
    return await service.refresh_access_token(refresh_token)

@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_in: UserCreate,
    service: AuthService = Depends(deps.get_auth_service)
):
    """
    Register a new user.
    """
    return await service.register_new_user(user_in)

def get_token(authorization: Annotated[str, Header()] = None):
    if not authorization:
        return None
    return authorization.split(" ")[1] if " " in authorization else authorization

@router.post("/logout")
async def logout(
    token: str = Depends(get_token),
    service: AuthService = Depends(deps.get_auth_service)
):
    if token: await service.logout(token)
    return {"message": "Logged out"}


# --- Google Auth ---

@router.get("/google/login")
def google_login(service: GoogleAuthService = Depends(deps.get_google_service)):
    """
    Redirect user to Google login page.
    """
    return RedirectResponse(service.get_login_url())

@router.get("/google/callback")
async def google_callback(
    code: str,
    service: GoogleAuthService = Depends(deps.get_google_service)
):
    """
    Google Callback after login.
    Redirect to frontend with token.
    """
    try:
        print(f"DEBUG: Ricevuto codice da Google: {code[:10]}...") # Log di debug
        
        token = await service.callback_handler(code)
        
        print(f"DEBUG: Token generato con successo per user: {token.user.username}") # Log di debug

        # URL frontend redirection with token params
        params = {
            "access_token": token.access_token,
            "refresh_token": token.refresh_token,
            "username": token.user.username,
            "full_name": token.user.full_name or ""
        }

        return RedirectResponse(f"{settings.FRONTEND_URL}?{urlencode(params)}")
        
    except Exception as e:
        return RedirectResponse(f"{settings.FRONTEND_URL}?error=access_denied")

# --- Utility ---
@router.get("/me", response_model=User)
def read_users_me(current_user: User = Depends(deps.get_current_user)):
    """
    Ritorna i dati dell'utente loggato (richiede Token).
    """
    return current_user
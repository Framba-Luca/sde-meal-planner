from fastapi import APIRouter, Depends, status
from fastapi.responses import RedirectResponse
from urllib.parse import urlencode
from pydantic import BaseModel

from src.core.config import settings
from src.schemas.token import Token
from src.schemas.user import User, UserCreate
from src.services.auth_service import AuthService
from src.services.oauth_service import GoogleAuthService
from src.api import deps

# Request models for JSON body
class LoginRequest(BaseModel):
    username: str
    password: str

router = APIRouter()

# --- Classic Auth ---

@router.post("/login", response_model=Token)
async def login_access_token(
    login_req: LoginRequest,
    service: AuthService = Depends(deps.get_auth_service)
):
    """
    Login endpoint accepting JSON body.
    """
    return await service.authenticate_user(login_req.username, login_req.password)

@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_in: UserCreate,
    service: AuthService = Depends(deps.get_auth_service)
):
    """
    Register a new user.
    """
    return await service.register_new_user(user_in)

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
    token_data = await service.callback_handler(code)
    
    # URL frontend redirection with token params
    params = {
        "token": token_data.access_token,
        "username": token_data.user.username,
        "full_name": token_data.user.full_name or ""
    }
    
    # Example: http://localhost:8501?token=xyz&username=mario
    return RedirectResponse(f"{settings.FRONTEND_URL}?{urlencode(params)}")

# --- Utility ---

@router.get("/me", response_model=User)
def read_users_me(current_user: User = Depends(deps.get_current_user)):
    """
    Ritorna i dati dell'utente loggato (richiede Token).
    """
    return current_user
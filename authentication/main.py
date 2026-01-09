"""
Authentication Service - REST API endpoints
"""
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Optional
from service import AuthService

app = FastAPI(title="Authentication Service", version="1.0.0")

# Initialize service
auth_service = AuthService()

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


# Pydantic models
class UserCreate(BaseModel):
    username: str
    password: str
    full_name: Optional[str] = None


class User(BaseModel):
    username: str
    full_name: str
    disabled: bool = False


class Token(BaseModel):
    access_token: str
    token_type: str
    user: User


class GoogleAuthRequest(BaseModel):
    code: str


class GoogleAuthUrlResponse(BaseModel):
    auth_url: str


# Dependency to get current user
async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """Get current authenticated user from token"""
    user_data = auth_service.get_current_user(token)
    if user_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return User(**user_data)


# Endpoints
@app.get("/")
async def root():
    """Root endpoint"""
    return {"service": "Authentication Service", "status": "running"}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.post("/register", response_model=User)
async def register(user: UserCreate):
    """Register a new user"""
    created_user = await auth_service.create_user(
        username=user.username,
        password=user.password,
        full_name=user.full_name
    )
    return User(
        username=created_user["username"],
        full_name=created_user["full_name"],
        disabled=created_user.get("disabled", False)
    )


@app.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    result = await auth_service.handle_login(form_data.username, form_data.password)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return Token(**result)


@app.get("/auth/google/url", response_model=GoogleAuthUrlResponse)
async def get_google_auth_url():
    """Get Google OAuth2 authorization URL"""
    auth_url = auth_service.get_google_auth_url()
    return GoogleAuthUrlResponse(auth_url=auth_url)


@app.post("/auth/google/callback", response_model=Token)
async def google_callback(request: GoogleAuthRequest):
    """Handle Google OAuth2 callback"""
    result = auth_service.handle_oauth_login(request.code)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to authenticate with Google"
        )
    return Token(**result)


@app.get("/users/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return current_user


@app.get("/verify")
async def verify_token(token: str):
    """Verify a token"""
    payload = auth_service.verify_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    return {"valid": True, "payload": payload}


@app.get("/users")
async def list_users():
    """List all registered users (for debugging/administration)"""
    users = []
    for username, user_data in auth_service.users_db.items():
        # Return user data without the hashed password
        users.append({
            "username": user_data["username"],
            "full_name": user_data["full_name"],
            "disabled": user_data["disabled"],
            "created_at": user_data["created_at"]
        })
    return {"users": users, "count": len(users)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

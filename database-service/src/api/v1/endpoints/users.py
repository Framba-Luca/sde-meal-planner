from fastapi import APIRouter, HTTPException, status
from src.schemas.user import UserCreate, UserResponse
from src.services.user_service import UserService

router = APIRouter()
user_service = UserService()

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate):
    """
    Create a new user.
    Public endpoint used by Authentication Service during registration.
    """
    # Check if username exists
    existing = user_service.get_user_by_username(user.username)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    user_id = user_service.create_user(user)
    if not user_id:
         raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )
        
    created_user = user_service.get_user_by_id(user_id)
    # Convert datetime for Pydantic compatibility if needed
    created_user['created_at'] = str(created_user['created_at'])
    return created_user

@router.get("/username/{username}")
async def get_user_by_username(username: str):
    """
    Retrieve user by username.
    Internal endpoint used by Auth Service for login (returns hashed_password).
    """
    user = user_service.get_user_by_username(username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user

@router.get("/", response_model=list[UserResponse])
async def get_users(skip: int = 0, limit: int = 100):
    """Retrieve a list of users with pagination."""
    users = user_service.get_users(skip=skip, limit=limit)
    for user in users:
        user['created_at'] = str(user['created_at'])
    return users

@router.get("/{user_id}", response_model=UserResponse)
async def get_user_by_id(user_id: int):
    """Retrieve user profile by ID."""
    user = user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    user['created_at'] = str(user['created_at'])
    return user
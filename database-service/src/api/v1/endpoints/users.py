from fastapi import APIRouter, HTTPException, Depends, status
from typing import List
from sqlmodel import Session

# Required imports
from src.core.database import get_session
from src.services.user_service import UserService
from src.schemas.user import UserCreate, UserResponse

router = APIRouter()

def get_user_service(session: Session = Depends(get_session)) -> UserService:
    return UserService(session)

# --- ROUTES ---

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user: UserCreate,
    # FastAPI injects the service instance with a working session
    service: UserService = Depends(get_user_service)
):
    # Check if the username already exists
    existing_user = service.get_user_by_username(user.username)
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    return service.create_user(user)


@router.get("/", response_model=List[UserResponse])
async def read_users(
    skip: int = 0,
    limit: int = 100,
    service: UserService = Depends(get_user_service)
):
    # Returns a paginated list of users
    return service.get_users(skip=skip, limit=limit)


@router.get("/username/{username}", response_model=UserResponse)
async def read_user_by_username(
    username: str,
    service: UserService = Depends(get_user_service)
):
    # Retrieve a user by username
    user = service.get_user_by_username(username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/{user_id}", response_model=UserResponse)
async def read_user_by_id(
    user_id: int,
    service: UserService = Depends(get_user_service)
):
    # Retrieve a user by primary key (ID)
    user = service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

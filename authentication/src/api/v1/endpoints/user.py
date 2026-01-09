from typing import List
from fastapi import APIRouter, Depends, HTTPException

from src.schemas.user import User
from src.api import deps
from src.infrastructure.user_client import UserRemoteRepository

router = APIRouter()

@router.get("/me", response_model=User)
def read_user_me(current_user: User = Depends(deps.get_current_user)):
    """
    Retrieves the profile of the currently logged-in user.
    """
    return current_user

@router.get("/", response_model=List[User])
async def read_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_user), # Requires login
    user_repo: UserRemoteRepository = Depends(deps.get_user_repo)
):
    """
    Retrieves the list of all users.
    """
    users = await user_repo.get_users(skip=skip, limit=limit)
    return users
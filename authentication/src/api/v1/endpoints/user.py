from typing import List
from fastapi import APIRouter, Depends, HTTPException

from src.schemas.user import User
from src.api import deps
from src.infrastructure.user_client import UserRemoteRepository

router = APIRouter()

@router.get("/", response_model=List[User])
async def read_users(
    skip: int = 0,
    limit: int = 100,
    user_repo: UserRemoteRepository = Depends(deps.get_user_repo)
):
    """
    Retrieves the list of all users.
    Note: The /me endpoint is in auth.py for consistency.
    """
    users = await user_repo.get_users(skip=skip, limit=limit)
    return users
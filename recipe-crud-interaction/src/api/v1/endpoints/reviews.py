from fastapi import APIRouter, Depends, HTTPException
from src.schemas.review import ReviewCreate
from src.services.review_service import ReviewService
from src.api.deps import get_review_service

router = APIRouter()

@router.get("/{recipe_id}")
async def get_reviews(recipe_id: int, service: ReviewService = Depends(get_review_service)):
    return service.get_reviews(recipe_id)

@router.post("/")
async def create_review(review: ReviewCreate, service: ReviewService = Depends(get_review_service)):
    user_id = 1 # TODO: Recuperare dal token in security.py
    res = service.create_review(user_id, review.dict())
    if "error" in res: raise HTTPException(400, res["error"])
    return res
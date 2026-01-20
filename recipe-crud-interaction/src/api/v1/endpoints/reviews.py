from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any
from src.schemas.review import ReviewCreate, ReviewResponse
from src.services.review_service import ReviewService
from src.api.deps import get_review_service, get_current_user

router = APIRouter()

@router.get("/recipe/{recipe_id}", response_model=List[ReviewResponse])
async def get_reviews(
    recipe_id: int,
    service: ReviewService = Depends(get_review_service)
):
    """
    Obtains all the reviews for a specific recipe
    """
    return service.get_reviews(recipe_id)

@router.post("/", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
async def create_review(
    review: ReviewCreate,
    service: ReviewService = Depends(get_review_service),
    current_user_id: int = Depends(get_current_user) # Requires Authentication
):
    """
    Creates a new revies
    Requires a valid JWT Token
    """
    result = service.create_review(user_id=current_user_id, data=review.dict())
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
        
    return result

@router.delete("/{review_id}")
async def delete_review(
    review_id: int,
    service: ReviewService = Depends(get_review_service),
    current_user_id: int = Depends(get_current_user) # Requires Login
):
    """
    Deletes a review
    """

    result = service.delete_review(current_user_id, review_id)
    
    if isinstance(result, dict) and "error" in result:
        code = result.get("code", 400)
        raise HTTPException(status_code=code, detail=result["error"])
        
    return {"status": "success", "message": "Review deleted"}
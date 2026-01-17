from typing import List, Dict
from fastapi import APIRouter, HTTPException, status, Depends
from src.schemas.review import ReviewCreate, ReviewResponse
from src.services.review_service import ReviewService
from src.api.deps import verify_internal_service_token

router = APIRouter()
review_service = ReviewService()

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_review(
    review: ReviewCreate,
    token_payload: Dict = Depends(verify_internal_service_token)
):
    """
    Saves a review in the DB.
    Return only the ID to keep it fast.
    """
    review_id = review_service.create_review(
        review.user_id, 
        review.recipe_id, 
        review.rating, 
        review.comment
    )
    
    if not review_id:
        raise HTTPException(status_code=500, detail="Failed to save review")
        
    return {"id": review_id, "status": "created"}

# QUI LA MODIFICA IMPORTANTE:
@router.get("/recipe/{recipe_id}", response_model=List[ReviewResponse]) 
async def get_reviews_by_recipe(
    recipe_id: int,
    token_payload: Dict = Depends(verify_internal_service_token)
):
    """
    Obtains all the reviews for a specific recipe.
    """
    reviews = review_service.get_reviews_by_recipe(recipe_id)
    
    return reviews
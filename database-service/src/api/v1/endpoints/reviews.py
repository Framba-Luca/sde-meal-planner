from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List
from sqlmodel import Session

from src.core.database import get_session
from src.services.review_service import ReviewService
from src.schemas.review import ReviewCreate, ReviewResponse

router = APIRouter()

# --- DEPENDENCY INJECTION ---
def get_review_service(session: Session = Depends(get_session)) -> ReviewService:
    return ReviewService(session)

# --- ROUTES ---

@router.get("/recipe/{recipe_id}", response_model=List[ReviewResponse])
async def get_reviews_by_recipe(
    recipe_id: str, 
    type: str = Query("auto", enum=["auto", "external", "internal"], description="Search mode: 'external' for MealDB, 'internal' for Custom recipes"),
    service: ReviewService = Depends(get_review_service)
):
    """
    Retrieves all reviews for a specific recipe.
    Uses the 'type' parameter to resolve ID collisions between Internal and External recipes.
    """
    # This calls the optimized method in your Service that handles the JOIN with User
    return service.get_reviews_by_recipe(recipe_identifier=recipe_id, search_mode=type)

@router.post("/", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
async def create_review(
    review: ReviewCreate,
    service: ReviewService = Depends(get_review_service)
):
    """
    Creates a new review.
    """
    review_id = service.create_review(
        user_id=review.user_id,
        recipe_id=review.recipe_id,
        rating=review.rating,
        comment=review.comment
    )
    # We fetch the created review to return it with the generated ID and timestamp
    return service.get_review_by_id(review_id)

@router.get("/{review_id}", response_model=ReviewResponse)
async def get_review(
    review_id: int,
    service: ReviewService = Depends(get_review_service)
):
    """
    Retrieves a single review by ID.
    """
    review = service.get_review_by_id(review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    return review

@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_review(
    review_id: int,
    service: ReviewService = Depends(get_review_service)
):
    """
    Deletes a review by its ID.
    Returns 204 No Content on success.
    """
    if not service.delete_review_raw(review_id):
        raise HTTPException(status_code=404, detail="Review not found")
    return
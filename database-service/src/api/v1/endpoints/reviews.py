from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlmodel import Session

from src.core.database import get_session
from src.services.review_service import ReviewService
from src.services.recipe_service import RecipeService  # Needed to find shadow recipes
from src.schemas.review import ReviewCreate, ReviewResponse

router = APIRouter()

# --- DEPENDENCY INJECTION ---
# Provides a ReviewService instance for each request
def get_review_service(session: Session = Depends(get_session)) -> ReviewService:
    return ReviewService(session)

# Provides a RecipeService instance for each request
def get_recipe_service(session: Session = Depends(get_session)) -> RecipeService:
    return RecipeService(session)


# --- ROUTES ---

@router.post("/", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
async def create_review(
    review: ReviewCreate,
    service: ReviewService = Depends(get_review_service)
):
    """
    Creates a new review for a given recipe by a user.
    Returns the full review after creation.
    """
    review_id = service.create_review(
        user_id=review.user_id,
        recipe_id=review.recipe_id,
        rating=review.rating,
        comment=review.comment
    )
    return service.get_review_by_id(review_id)

@router.get("/{review_id}", response_model=ReviewResponse)
async def get_review(
    review_id: int,
    service: ReviewService = Depends(get_review_service)
):
    """
    Retrieves a single review by ID.
    Essential for 'recipe-crud-interaction' to check ownership before deletion.
    """
    review = service.get_review_by_id(review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    return review

@router.get("/external/{external_id}", response_model=List[ReviewResponse])
async def get_reviews_by_external_id(
    external_id: str,
    review_service: ReviewService = Depends(get_review_service),
    recipe_service: RecipeService = Depends(get_recipe_service)
):
    """
    Retrieves all reviews for a shadow recipe identified by an external ID.
    Steps:
      1. Find the internal recipe ID from the external ID.
      2. Fetch all reviews for that internal recipe.
    Returns an empty list if no recipe is found.
    """
    recipe = recipe_service.get_recipe_by_external_id(external_id)
    if not recipe:
        return []
    return review_service.get_reviews_by_recipe(recipe.id)


@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_review(
    review_id: int,
    service: ReviewService = Depends(get_review_service)
):
    """
    Deletes a review by its ID.
    """
    if not service.delete_review_raw(review_id):
        raise HTTPException(status_code=404, detail="Review not found")
    return

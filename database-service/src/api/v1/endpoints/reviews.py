from typing import List
from fastapi import APIRouter, HTTPException, Depends
from src.services.review_service import ReviewService
# NESSUN BaseInternalClient qui!

router = APIRouter()
review_service = ReviewService()

@router.post("/", status_code=201)
async def create_review(payload: dict):
    result = review_service.create_review(
        user_id=payload['user_id'],
        recipe_id=payload.get('recipe_id'),
        external_id=payload.get('external_id'),
        rating=payload['rating'],
        comment=payload.get('comment')
    )
    if not result:
        raise HTTPException(status_code=500, detail="Errore inserimento DB")
    return {"id": result}

@router.get("/recipe/{recipe_id}")
async def get_reviews(recipe_id: int):
    return review_service.get_reviews_by_recipe(recipe_id)

@router.delete("/{review_id}")
async def delete_review(review_id: int):
    success = review_service.delete_review_raw(review_id)
    if not success:
         raise HTTPException(status_code=404, detail="Review not found")
    return {"status": "deleted"}
from fastapi import APIRouter
from src.api.v1.endpoints import recipes, review

api_router = APIRouter()
api_router.include_router(recipes.router, prefix="/recipes", tags=["Recipes"])
api_router.include_router(review.router, prefix="/reviews", tags=["Reviews"])
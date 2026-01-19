from fastapi import APIRouter
from src.api.v1.endpoints import users, meal_plans, recipes, reviews

api_router = APIRouter()

api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(meal_plans.router, prefix="/meal-plans", tags=["meal-plans"])
api_router.include_router(recipes.router, prefix="/recipes", tags=["recipes"])
api_router.include_router(reviews.router, prefix="/reviews", tags=["reviews"])
from fastapi import APIRouter
from src.api.v1.endpoints import users, meal_plans, recipes, security, reviews

api_router = APIRouter()

# Includiamo i router con i rispettivi prefissi e tag
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(meal_plans.router, prefix="/meal-plans", tags=["meal-plans"])
api_router.include_router(recipes.router, prefix="/recipes", tags=["recipes"])
api_router.include_router(security.router, prefix="/security", tags=["security"])
api_router.include_router(reviews.router, prefix="/reviews", tags=["reviews"])
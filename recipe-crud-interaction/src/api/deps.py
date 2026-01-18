from src.services.recipe_service import RecipeService
from src.services.review_service import ReviewService

def get_recipe_service() -> RecipeService:
    return RecipeService()

def get_review_service() -> ReviewService:
    return ReviewService()
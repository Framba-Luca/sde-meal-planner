from typing import List, Dict, Any, Optional
from src.core.config import settings
from src.services.base_client import BaseInternalClient
from src.services.recipe_service import RecipeService

class ReviewService(BaseInternalClient):
    def __init__(self):
        super().__init__()
        # Recipe Service to handle the Shadow Recipes
        self.recipe_service = RecipeService()
        self.db_service_url = f"{settings.DATABASE_SERVICE_URL}{settings.API_V1_STR}"

    def get_reviews_by_recipe(self, recipe_identifier: str, search_mode: str = "auto") -> List[Dict[str, Any]]:
        """
        Retrieves reviews from the DB Service using the safe search mode.
        """
        url = f"{self.db_service_url}/reviews/recipe/{recipe_identifier}"
        params = {"type": search_mode}
        
        response = self._req("GET", url, params=params)
        
        # Ensure response is a list to avoid Pydantic validation errors
        if isinstance(response, list):
            return response
            
        return []

    def get_reviews(self, recipe_id: int):
        return self.get_reviews_by_recipe(str(recipe_id), search_mode="auto")

    def get_review_by_id(self, review_id: int) -> Optional[Dict[str, Any]]:
        """Retrieves a review to check its existence"""
        return self._req("GET", f"{self.db_service_url}/reviews/{review_id}")

    def create_review(self, user_id: int, data: Dict[str, Any]):
        """
        Creates a review with the shadow logic
        """
        rid = data.get('recipe_id')
        ext_id = data.get('external_id')

        # SHADOW Logic: 
        # If we don't have an Internal Id but we have the external one,
        # ensure it exists in the DB.
        if not rid and ext_id:
            rid = self.recipe_service.ensure_shadow_recipe(ext_id)
        
        if not rid:
            return {"error": "Recipe not found (Shadow Import failed)."}

        payload = {
            "user_id": user_id,
            "recipe_id": rid,
            "rating": data.get('rating'),
            "comment": data.get('comment')
        }
        
        url = f"{self.db_service_url}/reviews/"
        result = self._req("POST", url, json=payload)
        
        return result if result else {"error": "Database save error"}

    def delete_review(self, user_id: int, review_id: int) -> Dict[str, Any]:
        """
        Deletes a review checking permissions
        """
        review = self.get_review_by_id(review_id)
        
        if not review or "user_id" not in review:
            return {"error": "Review not found", "code": 404}

        try:
            req_user_id = int(user_id)
            rev_user_id = int(review["user_id"])
        except (ValueError, TypeError):
            return {"error": "Invalid ID format", "code": 400}

        # Is user the owner of review?
        if rev_user_id == req_user_id:
            return self._req("DELETE", f"{self.db_service_url}/reviews/{review_id}")

        # Is user owner of recipe?
        recipe_id = review.get("recipe_id")
        if recipe_id:
            recipe = self.recipe_service.get_recipe(recipe_id)
            if recipe and recipe.get("user_id"):
                if int(recipe["user_id"]) == req_user_id:
                     return self._req("DELETE", f"{self.db_service_url}/reviews/{review_id}")

        return {"error": "Permission denied. You are not the review author nor the recipe owner.", "code": 403}
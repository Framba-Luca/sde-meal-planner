from typing import List, Dict, Any, Optional
from fastapi import HTTPException, status
from src.core.config import settings
from src.services.base_client import BaseInternalClient
from src.services.recipe_service import RecipeService

class ReviewService(BaseInternalClient):
    def __init__(self):
        super().__init__()
        # Recipe Service to handle the Shadow Recipes
        self.recipe_service = RecipeService()
        self.db_service_url = f"{settings.DATABASE_SERVICE_URL}{settings.API_V1_STR}"

    def get_reviews(self, recipe_id: int):
        """To obtain the reviews from the DB Service"""
        url = f"{self.db_service_url}/reviews/recipe/{recipe_id}"
        return self._req("GET", url) or []
    
    def get_review_by_id(self, review_id: int) -> Optional[Dict[str, Any]]:
        """Retireve a review to check its existence"""
        return self._req("GET", f"{self.db_service_url}/reviews/{review_id}")

    def create_review(self, user_id: int, data: Dict[str, Any]):
        """
        Create a review with the shadow logic
        """
        rid = data.get('recipe_id')
        ext_id = data.get('external_id')

        # SHADOW Logic:
        # If we don't have an Internal Id but we have the external one of TheMealDB
        # it's needed to assure that the id exists in the DB.
        if not rid and ext_id:
            print(f"DEBUG: Importazione Shadow Recipe per {ext_id} prima della recensione...")
            rid = self.recipe_service.ensure_shadow_recipe(ext_id)
        
        if not rid:
            return {"error": "Recipe not found (Shadow Import failed)."}

        # Construct the payload for the database service
        payload = {
            "user_id": user_id,       # Injected by the token
            "recipe_id": rid,         # Internal Id
            "rating": data['rating'],
            "comment": data.get('comment')
        }
        
        url = f"{self.db_service_url}/reviews/"
        result = self._req("POST", url, json=payload)
        
        return result if result else {"error": "Errore salvataggio DB"}

    def delete_review(self, user_id: int, review_id: int) -> Dict[str, Any]:
        """
        Delete the reviews
        IMPORTANTE: Verifica prima che la recensione appartenga all'utente corrente.
        """
        review = self.get_review_by_id(review_id)
        
        if not review:
            return {"error": "Review not found", "code": 404}

        # Is user the owrer of review?
        if int(review.get("user_id")) == int(user_id):
            # Yeah
            return self._req("DELETE", f"{self.db_service_url}/reviews/{review_id}")

        # Is user owner of recipe?
        recipe_id = review.get("recipe_id")
        recipe = self.recipe_service.get_recipe(recipe_id)
        
        if recipe and int(recipe.get("user_id")) == int(user_id):
            # Yeah, the user can moderate the reviews
            return self._req("DELETE", f"{self.db_service_url}/reviews/{review_id}")

        # If we arrive here the user doesn't have any rights off ownership
        return {"error": "Permission denied. You are not the review author nor the recipe owner.", "code": 403}
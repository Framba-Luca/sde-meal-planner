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

    def get_reviews(self, recipe_id: int):
        """To obtain the reviews from the DB Service"""
        url = f"{settings.DATABASE_SERVICE_URL}{settings.API_V1_STR}/reviews/recipe/{recipe_id}"
        return self._req("GET", url) or []

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
            return {"error": "Impossibile trovare la ricetta specificata (Shadow Import fallito)."}

        # Construct the payload for the database service
        payload = {
            "user_id": user_id,       # Injected by the token
            "recipe_id": rid,         # Internal Id
            "rating": data['rating'],
            "comment": data.get('comment')
        }
        
        url = f"{settings.DATABASE_SERVICE_URL}{settings.API_V1_STR}/reviews/"
        result = self._req("POST", url, json=payload)
        
        return result if result else {"error": "Errore salvataggio DB"}

    def delete_review(self, review_id: int, current_user_id: int) -> bool:
        """
        Delete the reviews
        IMPORTANTE: Verifica prima che la recensione appartenga all'utente corrente.
        """
        url = f"{settings.DATABASE_SERVICE_URL}{settings.API_V1_STR}/reviews/{review_id}"
        
        res = self._req("DELETE", url)
        return res is not None
from typing import Dict, Any
from src.core.config import settings
from src.services.recipe_service import RecipeService
import requests

class ReviewService:
    def __init__(self):
        self.recipe_service = RecipeService()
        self.headers = {"Authorization": f"Bearer {settings.INTERNAL_SERVICE_SECRET}"}

    def get_reviews(self, recipe_id: int):
        url = f"{settings.DATABASE_SERVICE_URL}/api/v1/reviews/recipe/{recipe_id}"
        try:
            r = requests.get(url, headers=self.headers)
            r.raise_for_status()
            return r.json()
        except:
            return []

    def create_review(self, user_id: int, data: Dict[str, Any]):
        rid = data.get('recipe_id')
        ext_id = data.get('external_id')

        # Se è una ricetta esterna, assicuriamoci che esista come Shadow nel DB
        if not rid and ext_id:
            rid = self.recipe_service.ensure_shadow_recipe(ext_id)
        
        if not rid:
            return {"error": "Recipe not found"}

        payload = {
            "user_id": user_id,
            "recipe_id": rid,
            "rating": data['rating'],
            "comment": data.get('comment') or data.get('review')
        }
        
        url = f"{settings.DATABASE_SERVICE_URL}/api/v1/reviews/"
        try:
            r = requests.post(url, json=payload, headers=self.headers)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            return {"error": str(e)}
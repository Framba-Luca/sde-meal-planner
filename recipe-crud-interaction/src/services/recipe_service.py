import requests
from typing import Dict, Optional, Any, List
from src.core.config import settings
from src.services.base_client import BaseInternalClient
import json
import redis

class RecipeService(BaseInternalClient):

    def __init__(self):
        super().__init__()
        self.cache = redis.Redis(
            host=settings.REDIS_HOST, 
            port=settings.REDIS_PORT, 
            decode_responses=True
        )
        self.fetch_service_url = settings.RECIPES_FETCH_SERVICE_URL
        self.db_service_url = f"{settings.DATABASE_SERVICE_URL}{settings.API_V1_STR}"
        
    def get_user_recipes(self, user_id: int):
        return self._req("GET", f"{settings.DATABASE_SERVICE_URL}/api/v1/recipes/user/{user_id}") or []

    def create_recipe(self, user_id: int, data: Dict):
        url = f"{settings.DATABASE_SERVICE_URL}/api/v1/recipes"
        return self._req("POST", url, {"user_id": user_id, **data})

    def get_recipe(self, recipe_id: int):
        return self._req("GET", f"{settings.DATABASE_SERVICE_URL}/api/v1/recipes/{recipe_id}")

    def update_recipe(self, recipe_id: int, data: Dict):
        return self._req("PUT", f"{settings.DATABASE_SERVICE_URL}/api/v1/recipes/{recipe_id}", data)

    def delete_recipe(self, recipe_id: int):
        return self._req("DELETE", f"{settings.DATABASE_SERVICE_URL}/api/v1/recipes/{recipe_id}")

    def get_recipe_details(self, external_id: str) -> Optional[Dict[str, Any]]:
        resp = requests.get(f"{self.fetch_service_url}/recipe/{external_id}")
        return resp.json() if resp.status_code == 200 else None
    
    def ensure_shadow_recipe(self, external_id: str) -> Optional[int]:
        """
        Transform an external recipe into a shadow one 
        """
        check = self._req("GET", f"{self.db_service_url}/recipes/external/{external_id}")
        
        if check and "id" in check:
            return check["id"]

        ext_data = requests.get(f"{self.fetch_service_url}/lookup/{external_id}").json()
        
        payload = {
            "external_id": external_id,
            "name": ext_data['meals'][0]['strMeal'],
            "category": ext_data['meals'][0].get('strCategory')
        }
        new_recipe = self._req("POST", f"{self.db_service_url}/recipes/shadow", json=payload)
        return new_recipe.get("id")
        
    def search_unified(self, query: str) -> List[Dict[str, Any]]:
        
        results = []
        known_external_ids = set()

        try:
            internal_resp = self._req("GET", f"{self.db_service_url}/recipes/search", params={"q": query})
            internal_data = internal_resp if isinstance(internal_resp, list) else []

            for r in internal_data:
                if r.get("external_id"):
                    known_external_ids.add(str(r["external_id"]))

                results.append({
                    "name": r.get("name"),
                    "id_recipe": r.get("id"),
                    "id_external": r.get("external_id"),
                    "is_external": False
                })
        except Exception as e:
            print(f"Internal Search Error: {e}")

        try:
            ext_resp = requests.get(f"{self.fetch_service_url}/search/name/{query}", timeout=5)
            if ext_resp.status_code == 200:
                ext_data = ext_resp.json().get("meals", [])
                
                for m in ext_data:
                    ext_id = str(m.get("id_external"))

                    if ext_id in known_external_ids:
                        continue

                    results.append({
                        "name": m.get("nome"),
                        "id_recipe": None,
                        "id_esterno": ext_id,
                        "is_external": True
                    })
        except Exception as e:
            print(f"External Search Error: {e}")

        return results
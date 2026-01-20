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
        # Assicuriamoci che l'user_id sia nel payload
        return self._req("POST", url, {"user_id": user_id, **data})

    def get_recipe(self, recipe_id: int):
        return self._req("GET", f"{settings.DATABASE_SERVICE_URL}/api/v1/recipes/{recipe_id}")

    def update_recipe(self, user_id: int, recipe_id: int, data: Dict) -> Dict[str, Any]:
        existing_recipe = self.get_recipe(recipe_id)
        
        if not existing_recipe:
            return {"error": "Recipe not found", "code": 404}
        
        if int(existing_recipe.get("user_id")) != int(user_id):
            return {"error": "Permission denied. You do not own this recipe.", "code": 403}

        return self._req("PUT", f"{self.db_service_url}/recipes/{recipe_id}", data)

    def delete_recipe(self, user_id: int, recipe_id: int) -> Dict[str, Any]:
        existing_recipe = self.get_recipe(recipe_id)
        
        if not existing_recipe:
            return {"error": "Recipe not found", "code": 404}
            
        if int(existing_recipe.get("user_id")) != int(user_id):
            return {"error": "Permission denied. You do not own this recipe.", "code": 403}

        return self._req("DELETE", f"{self.db_service_url}/recipes/{recipe_id}")
    
    def get_recipe_details(self, external_id: str) -> Optional[Dict[str, Any]]:
        try:
            resp = requests.get(f"{self.fetch_service_url}/recipe/{external_id}", timeout=5)
            return resp.json() if resp.status_code == 200 else None
        except Exception:
            return None
    
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
        
    def search_unified(
        self, 
        query: Optional[str] = None,
        category: Optional[str] = None,
        area: Optional[str] = None,
        ingredient: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        
        results = []
        known_external_ids = set()

        # 1. INTERNAL DB SEARCH
        # ---------------------
        db_params = {}
        if query: db_params["q"] = query
        if category: db_params["category"] = category
        if area: db_params["area"] = area
        if ingredient: db_params["ingredient"] = ingredient

        try:
            internal_resp = self._req("GET", f"{self.db_service_url}/recipes/search", params=db_params)
            internal_data = internal_resp if isinstance(internal_resp, list) else []

            for r in internal_data:
                if r.get("external_id"):
                    known_external_ids.add(str(r["external_id"]))

                results.append({
                    "id": r.get("id"),
                    "external_id": r.get("external_id"),
                    "name": r.get("name"),
                    "image": r.get("image"),
                    "category": r.get("category"),
                    "area": r.get("area"),
                    "instructions": r.get("instructions"),
                    "is_custom": r.get("is_custom", True),
                    "source": "internal"
                })
        except Exception as e:
            print(f"⚠️ Internal Search Error: {e}")

        # 2. EXTERNAL SEARCH (TheMealDB)
        # ------------------------------
        ext_endpoint = ""
        
        if query:
            ext_endpoint = f"/search/name/{query}"
        elif ingredient:
            ext_endpoint = f"/filter?i={ingredient}"
        elif category:
            ext_endpoint = f"/filter?c={category}"
        elif area:
            ext_endpoint = f"/filter?a={area}"
            
        if ext_endpoint:
            try:
                url = f"{self.fetch_service_url}{ext_endpoint}"
                ext_resp = requests.get(url, timeout=5)
                
                if ext_resp.status_code == 200:
                    data = ext_resp.json()
                    meals = data.get("meals") or []
                    
                    for m in meals:
                        ext_id = str(m.get("idMeal"))
                        if ext_id in known_external_ids:
                            continue

                        res_category = m.get("strCategory") or category
                        res_area = m.get("strArea") or area

                        results.append({
                            "id": None,
                            "external_id": ext_id,
                            "name": m.get("strMeal"),
                            "image": m.get("strMealThumb"),
                            "category": res_category,
                            "area": res_area,
                            "instructions": m.get("strInstructions"),
                            "is_custom": False,
                            "source": "external"
                        })
            except Exception as e:
                print(f"⚠️ External Search Error: {e}")

        return results
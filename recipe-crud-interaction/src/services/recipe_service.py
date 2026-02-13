import requests
from typing import Dict, Optional, Any, List
from src.core.config import settings
from src.services.base_client import BaseInternalClient
import json
import redis
import hashlib

class RecipeService(BaseInternalClient):

    # Redis Initiaalization

    def __init__(self):
        super().__init__()
        self.cache = redis.Redis(
            host=settings.REDIS_HOST, 
            port=settings.REDIS_PORT, 
            decode_responses=True
        )
        self.fetch_service_url = settings.RECIPES_FETCH_SERVICE_URL
        self.db_service_url = f"{settings.DATABASE_SERVICE_URL}{settings.API_V1_STR}"
        self.CACHE_TTL = 3600

    def _safe_cache_get(self, key: str):
        try:
            data = self.cache.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            print(f"⚠️ Redis Get Error: {e}")
            return None

    def _safe_cache_set(self, key: str, value: Any, ttl: int = None):
        try:
            self.cache.setex(key, ttl or self.CACHE_TTL, json.dumps(value))
        except Exception as e:
            print(f"⚠️ Redis Set Error: {e}")

    def _safe_cache_delete(self, *keys):
        try:
            if keys:
                self.cache.delete(*keys)
        except Exception as e:
            print(f"⚠️ Redis Delete Error: {e}")

    # --- RECIPE OPERATIONS --- #
        
    def get_user_recipes(self, user_id: int):
        cache_key = f"recipes:user:{user_id}"
        cached = self._safe_cache_get(cache_key)
        if cached is not None:
            return cached

        data = self._req("GET", f"{settings.DATABASE_SERVICE_URL}/api/v1/recipes/user/{user_id}") or []
        self._safe_cache_set(cache_key, data, ttl=1800)
        return data

    def create_recipe(self, user_id: int, data: Dict):
        url = f"{settings.DATABASE_SERVICE_URL}/api/v1/recipes"
        result = self._req("POST", url, {"user_id": user_id, **data})
        
        self._safe_cache_delete(f"recipes:user:{user_id}")
        return result

    def get_recipe(self, recipe_id: int, source: str = None):
        """
        Orchestrates recipe retrieval.
        If source="external", it skips the local DB and goes straight to the fetch service.
        Otherwise, it tries the DB first, then falls back to external.
        """
        
        cache_key = f"recipe:{source or 'auto'}:{recipe_id}"
        cached = self._safe_cache_get(cache_key)
        if cached:
            return cached

        # 1. External explicit
        if source == "external":
            result = self._fetch_external_recipe(recipe_id)
            if result:
                self._safe_cache_set(cache_key, result, ttl=86400) # 24h per le esterne (non cambiano)
            return result

        # 2. Internal DB
        try:
            internal_recipe = self._req("GET", f"{self.db_service_url}/recipes/{recipe_id}")
            if internal_recipe and "id" in internal_recipe:
                internal_recipe["source"] = "internal"
                self._safe_cache_set(cache_key, internal_recipe, ttl=1800)
                return internal_recipe
        except Exception:
            pass

        # 3. Fallback: External
        result = self._fetch_external_recipe(recipe_id)
        if result:
            self._safe_cache_set(cache_key, result, ttl=86400)
        return result

    def _fetch_external_recipe(self, recipe_id):
        """Helper to fetch from external service"""
        try:
            url = f"{self.fetch_service_url}/recipe/{recipe_id}"
            ext_resp = requests.get(url, timeout=5)
            if ext_resp.status_code == 200:
                data = ext_resp.json()
                return {
                    "id": None,
                    "external_id": str(data.get("id_external")),
                    "name": data.get("name"),
                    "image": data.get("image"),
                    "category": data.get("category"),
                    "area": data.get("area"),
                    "instructions": data.get("instructions"),
                    "is_custom": False,
                    "source": "external",
                    "ingredients": data.get("ingredients", [])
                }
        except Exception as e:
            print(f"⚠️ Error fetching external recipe: {e}")
        return None

    def update_recipe(self, user_id: int, recipe_id: int, data: Dict) -> Dict[str, Any]:
        existing_recipe = self.get_recipe(recipe_id)
        if not existing_recipe:
            return {"error": "Recipe not found", "code": 404}
        if existing_recipe.get("source") == "external":
             return {"error": "Cannot update external recipes directly.", "code": 403}
        if int(existing_recipe.get("user_id")) != int(user_id):
            return {"error": "Permission denied. You do not own this recipe.", "code": 403}

        result = self._req("PUT", f"{self.db_service_url}/recipes/{recipe_id}", data)
        
        self._safe_cache_delete(
            f"recipe:internal:{recipe_id}",
            f"recipe:auto:{recipe_id}",
            f"recipes:user:{user_id}"
        )
        return result

    def delete_recipe(self, user_id: int, recipe_id: int) -> Dict[str, Any]:
        existing_recipe = self.get_recipe(recipe_id)
        if not existing_recipe:
            return {"error": "Recipe not found", "code": 404}
        if int(existing_recipe.get("user_id")) != int(user_id):
            return {"error": "Permission denied. You do not own this recipe.", "code": 403}

        result = self._req("DELETE", f"{self.db_service_url}/recipes/{recipe_id}")
        
        # INVALIDAZIONE CACHE
        self._safe_cache_delete(
            f"recipe:internal:{recipe_id}",
            f"recipe:auto:{recipe_id}",
            f"recipes:user:{user_id}"
        )
        return result
    
    def ensure_shadow_recipe(self, external_id: str) -> Optional[int]:
        """
        Transform an external recipe into a shadow one (Keep this for reviews)
        """
        check = self._req("GET", f"{self.db_service_url}/recipes/external/{external_id}")
        if check and "id" in check:
            return check["id"]

        ext_data = self._fetch_external_recipe(external_id)
        if not ext_data:
            return None
        
        payload = {
            "external_id": external_id,
            "name": ext_data['name'],
            "category": ext_data.get('category')
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
        
        params_str = f"{query}-{category}-{area}-{ingredient}"
        cache_key = f"search:{hashlib.md5(params_str.encode()).hexdigest()}"
        
        cached = self._safe_cache_get(cache_key)
        if cached is not None:
            return cached

        results = []
        known_external_ids = set()

        # 1. Internal Search
        db_params = {}
        if query: db_params["query"] = query
        if category: db_params["category"] = category
        if area: db_params["area"] = area
        if ingredient: db_params["ingredient"] = ingredient

        try:
            internal_resp = self._req("GET", f"{self.db_service_url}/recipes", params=db_params)
            internal_data = internal_resp if isinstance(internal_resp, list) else []

            for r in internal_data:
                if r.get("external_id"):
                    known_external_ids.add(str(r["external_id"]))
                r["source"] = "internal"
                results.append(r)
        except Exception as e:
            print(f"⚠️ Internal Search Error: {e}")

        # 2. External Search
        url = ""
        if query: url = f"{self.fetch_service_url}/search/name/{query}"
        elif category: url = f"{self.fetch_service_url}/filter/category/{category}"
        elif area: url = f"{self.fetch_service_url}/filter/area/{area}"
        elif ingredient: url = f"{self.fetch_service_url}/filter/ingredient/{ingredient}"
            
        if url:
            try:
                ext_resp = requests.get(url, timeout=5)
                if ext_resp.status_code == 200:
                    data = ext_resp.json()
                    meals = data.get("meals", [])
                    for m in meals:
                        ext_id = str(m.get("id_external"))
                        if ext_id in known_external_ids: continue
                        
                        results.append({
                            "id": None,
                            "external_id": ext_id,
                            "name": m.get("name"),
                            "image": m.get("image"),
                            "category": m.get("category"),
                            "area": m.get("area"),
                            "instructions": m.get("instructions"),
                            "is_custom": False,
                            "source": "external"
                        })
            except Exception as e:
                print(f"⚠️ External Search Connection Error: {e}")

        self._safe_cache_set(cache_key, results, ttl=300)
        return results
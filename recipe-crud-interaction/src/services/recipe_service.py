import requests
from typing import Dict, Optional, Any, List
from src.core.config import settings
from src.services.base_client import BaseInternalClient
from src.core.cache import cache_client
import hashlib
import random

class RecipeService(BaseInternalClient):

    def __init__(self):
        super().__init__()
        self.fetch_service_url = settings.RECIPES_FETCH_SERVICE_URL
        self.db_service_url = f"{settings.DATABASE_SERVICE_URL}{settings.API_V1_STR}"

    # --- RECIPE OPERATIONS --- #
        
    def get_user_recipes(self, user_id: int):
        cache_key = f"recipes:user:{user_id}"
        
        cached = cache_client.get(cache_key)
        if cached is not None:
            return cached

        data = self._req("GET", f"{settings.DATABASE_SERVICE_URL}/api/v1/recipes/user/{user_id}") or []
        cache_client.set(cache_key, data, ttl=1800)
        return data

    def create_recipe(self, user_id: int, data: Dict):
        url = f"{settings.DATABASE_SERVICE_URL}/api/v1/recipes"
        result = self._req("POST", url, {"user_id": user_id, **data})
        
        cache_client.delete(f"recipes:user:{user_id}")
        return result

    def get_recipe(self, recipe_id: int, source: str = None):
        """
        Orchestrates recipe retrieval.
        If source="external", it skips the local DB and goes straight to the fetch service.
        Otherwise, it tries the DB first, then falls back to external.
        """
        cache_key = f"recipe:{source or 'auto'}:{recipe_id}"
        
        cached = cache_client.get(cache_key)
        if cached:
            return cached

        # 1. External explicit
        if source == "external":
            result = self._fetch_external_recipe(recipe_id)
            if result:
                cache_client.set(cache_key, result, ttl=86400) # 24h for external
            return result

        # 2. Internal DB
        try:
            internal_recipe = self._req("GET", f"{self.db_service_url}/recipes/{recipe_id}")
            if internal_recipe and "id" in internal_recipe:
                internal_recipe["source"] = "internal"
                cache_client.set(cache_key, internal_recipe, ttl=1800)
                return internal_recipe
        except Exception:
            pass

        # 3. Fallback: External
        result = self._fetch_external_recipe(recipe_id)
        if result:
            cache_client.set(cache_key, result, ttl=86400)
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
        except Exception:
            # Fallback gracefully on external service errors
            pass
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
        
        cache_client.delete(
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
        
        cache_client.delete(
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
        
        cached = cache_client.get(cache_key)
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
        except Exception:
            # Internal search failed, will try external
            pass

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
            except Exception:
                # External search failed, continue with internal results
                pass

        cache_client.set(cache_key, results, ttl=300)
        return results
    
    # --- NEW METHODS FOR MEAL PROPOSER SUPPORT ---

    def get_categories(self) -> List[str]:
        """
        Proxy method to get categories from Fetch Service.
        Cached for performance.
        """
        cache_key = "metadata:categories"
        cached = cache_client.get(cache_key)
        if cached: return cached

        # Call Fetch Service
        url = f"{self.fetch_service_url}/categories"
        try:
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                data = resp.json().get("categories", [])
                cache_client.set(cache_key, data, ttl=86400) # 24h cache
                return data
        except Exception:
            # Metadata fetch failed, return empty
            pass
        return []

    def get_areas(self) -> List[str]:
        """Proxy method to get areas from Fetch Service"""
        cache_key = "metadata:areas"
        cached = cache_client.get(cache_key)
        if cached: return cached

        url = f"{self.fetch_service_url}/areas"
        try:
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                data = resp.json().get("areas", [])
                cache_client.set(cache_key, data, ttl=86400)
                return data
        except Exception:
            # Metadata fetch failed, return empty
            pass
        return []

    # ---------------------------------------------------------
    # RANDOM RECIPE LOGIC (Internal + External Mix)
    # ---------------------------------------------------------

    def get_random_recipe(self) -> Optional[Dict[str, Any]]:
        """
        Retrieves a random recipe.
        Randomly decides whether to fetch from Internal DB or External API.
        Returns data matching RecipeUnifiedDetail schema.
        """
        # 50% chance to pick Internal or External
        source_choice = random.choice(["internal", "external"])
        recipe = None



        if source_choice == "internal":
            recipe = self._get_random_internal()
            # Fallback to external if internal DB is empty or fails
            if not recipe:
                recipe = self._get_random_external()
        else:
            recipe = self._get_random_external()
            # Fallback to internal if external API fails
            if not recipe:
                 recipe = self._get_random_internal()

        return recipe

    def _get_random_internal(self) -> Optional[Dict[str, Any]]:
        """Helper to fetch random recipe from Database Service"""
        try:
            # Calls GET /api/v1/recipes/random in database-service
            # Ensure your database-service has this endpoint!
            response = self._req("GET", f"{self.db_service_url}/recipes/random")
            
            if not response or not isinstance(response, dict):
                return None
                
            if "id" not in response:
                return None
            
            # Ensure user_id is valid (skip if None for shadow recipes)
            user_id = response.get("user_id")
            if user_id is None:
                return None  # Skip shadow recipes in random fetch
            
            # Map to RecipeUnifiedDetail structure
            return {
                "id": response.get("id"),
                "external_id": str(response.get("external_id")) if response.get("external_id") else None,
                "name": response.get("name"),
                "image": response.get("image"),
                "category": response.get("category"),
                "area": response.get("area"),
                "instructions": response.get("instructions"),
                "ingredients": response.get("ingredients", []),
                "is_custom": True,
                "source": "internal"
            }
        except Exception:
            # Internal random failed, fallback will be triggered
            pass
        return None

    def _get_random_external(self) -> Optional[Dict[str, Any]]:
        """Helper to fetch random recipe from Fetch Service"""
        try:
            # Calls GET /random in recipe-fetch-service
            url = f"{self.fetch_service_url}/random" 
            resp = requests.get(url, timeout=5)
            
            if resp.status_code == 200:
                data = resp.json()
                
                # Handle case where API returns a list or a single object
                item = None
                if isinstance(data, list) and len(data) > 0:
                    item = data[0]
                elif isinstance(data, dict):
                    item = data
                
                if item:
                    # Use the helper to map to unified format
                    return self._map_external_to_unified(item)
                    
        except Exception:
            # External random failed, return None
            pass
        return None

    def _map_external_to_unified(self, ext_data: Dict) -> Dict:
        """Helper to format external data to unified format"""
        return {
            "id": None,
            "external_id": str(ext_data.get("id_external") or ext_data.get("idMeal")),
            "name": ext_data.get("name") or ext_data.get("strMeal"),
            "image": ext_data.get("image") or ext_data.get("strMealThumb"),
            "category": ext_data.get("category") or ext_data.get("strCategory"),
            "area": ext_data.get("area") or ext_data.get("strArea"),
            "instructions": ext_data.get("instructions") or ext_data.get("strInstructions"),
            "is_custom": False,
            "source": "external",
            # Flatten ingredients if necessary or pass as is
            "ingredients": ext_data.get("ingredients", []) 
        }
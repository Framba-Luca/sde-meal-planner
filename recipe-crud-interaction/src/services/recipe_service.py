import requests
from typing import Dict, Optional
from src.core.config import settings

class RecipeService:
    def __init__(self):
        self.headers = {"Authorization": f"Bearer {settings.INTERNAL_SERVICE_SECRET}"}

    def _req(self, method: str, url: str, data: Optional[Dict] = None):
        try:
            if method == "GET": r = requests.get(url, headers=self.headers)
            elif method == "POST": r = requests.post(url, json=data, headers=self.headers)
            elif method == "PUT": r = requests.put(url, json=data, headers=self.headers)
            elif method == "DELETE": r = requests.delete(url, headers=self.headers)
            else: return None
            r.raise_for_status()
            return r.json()
        except Exception as e:
            print(f"Error calling {url}: {e}")
            return None

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

    # --- Shadow Logic ---
    def ensure_shadow_recipe(self, external_id: str) -> Optional[int]:
        # 1. Check DB
        existing = self._req("GET", f"{settings.DATABASE_SERVICE_URL}/api/v1/recipes/external/{external_id}")
        if existing and existing.get('id'): return existing['id']

        # 2. Fetch External
        try:
            fetch_url = f"{settings.RECIPES_FETCH_SERVICE_URL}/recipe/{external_id}"
            resp = requests.get(fetch_url) # Internal service, direct call
            if resp.status_code == 404: return None
            data = resp.json()
            if "meals" in data and data["meals"]: data = data["meals"][0]
        except Exception: return None

        # 3. Create Shadow
        payload = {
            "name": data.get('name') or data.get('strMeal'),
            "image": data.get('image') or data.get('strMealThumb'),
            "external_id": str(external_id),
            "category": data.get('category') or data.get('strCategory'),
            "area": data.get('area') or data.get('strArea')
        }
        res = self._req("POST", f"{settings.DATABASE_SERVICE_URL}/api/v1/recipes/shadow", payload)
        return res['id'] if res else None
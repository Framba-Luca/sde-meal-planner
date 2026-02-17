"""
Meal Proposer Service - Proposes recipes interfacing with the Recipe CRUD Gateway
"""
from typing import Dict, Any, List, Optional
import requests
import os

RECIPE_CRUD_URL = os.getenv("RECIPE_CRUD_URL", "http://recipe-crud-interaction:8000")

class MealProposerService:
    """Service for proposing meals from the central Gateway (Internal & External)"""
    
    def __init__(self):
        # L'URL base punta alla root delle API v1 definite in recipes.py
        self.api_url = f"{RECIPE_CRUD_URL}/api/v1/recipes"
    
    def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Any]:
        """Make a request to Recipe Gateway API"""
        try:
            url = f"{self.api_url}/{endpoint}"
            # print(f"DEBUG: Calling {url} with params {params}")
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error making request to Recipe Gateway: {e}")
            if hasattr(e.response, 'status_code'):
                print(f"  Status Code: {e.response.status_code}")
                try:
                    print(f"  Response: {e.response.text[:500]}")
                except:
                    pass
            return None

    def search_smart(self, query: str) -> Optional[List[Dict[str, Any]]]:
        """
        Smart search: Tries to find recipes by Ingredient, then Category, then Area.
        Calls the Gateway endpoint: GET /search (defined in recipes.py)
        Returns: List of Summaries (ID, Name, Image, but NO ingredients/instructions)
        """
        print(f"DEBUG: Attempting smart search for '{query}'")

        # 1. Try by Ingredient
        # recipes.py defines query param 'ingredient'
        results = self._make_request("search", params={"ingredient": query})
        if results and isinstance(results, list) and len(results) > 0:
            return [self.format_recipe(r) for r in results]
        
        # 2. Try by Category (Fallback)
        # recipes.py defines query param 'category'
        results = self._make_request("search", params={"category": query})
        if results and isinstance(results, list) and len(results) > 0:
            return [self.format_recipe(r) for r in results]

        # 3. Try by Area/Cuisine (Fallback)
        # recipes.py defines query param 'area'
        results = self._make_request("search", params={"area": query})
        if results and isinstance(results, list) and len(results) > 0:
            return [self.format_recipe(r) for r in results]
            
        return None

    def search_by_ingredient(self, ingredient: str) -> Optional[List[Dict[str, Any]]]:
        """Wrapper for smart search"""
        return self.search_smart(ingredient)
    
    def get_recipe_by_id(self, meal_id: str) -> Optional[Dict[str, Any]]:
        """
        Get full recipe details by ID.
        Calls Gateway endpoint: GET /{recipe_id} (defined in recipes.py)
        Returns: Full Detail object with ingredients and instructions.
        """
        result = self._make_request(f"{meal_id}")
        if result:
            return self.format_recipe(result)
        return None

    def get_random_meal(self) -> Optional[Dict[str, Any]]:
        """
        Get a random recipe.
        Calls Gateway endpoint: GET /random (defined in recipes.py)
        """
        result = self._make_request("random")
        
        if isinstance(result, list) and result:
             return self.format_recipe(result[0])
        elif isinstance(result, dict):
             return self.format_recipe(result)
        return None
    
    def format_recipe(self, recipe: Dict[str, Any]) -> Dict[str, Any]:
        """
        Adapter: Converts Gateway Response -> Frontend Format.
        Robustly handles missing ingredients by checking for raw fields.
        """
        r_id = recipe.get("id")
        if not r_id:
            r_id = recipe.get("external_id")

        final_ingredients = []

        has_flat_ingredients = any(f"strIngredient{i}" in recipe for i in range(1, 4))
        
        if has_flat_ingredients:
            for i in range(1, 21):
                ing_key = f"strIngredient{i}"
                meas_key = f"strMeasure{i}"
                
                ing_val = recipe.get(ing_key)
                meas_val = recipe.get(meas_key)
                
                if ing_val and ing_val.strip():
                    final_ingredients.append({
                        "ingredient": ing_val.strip(),
                        "measure": (meas_val or "").strip()
                    })

        if not final_ingredients and "ingredients" in recipe and isinstance(recipe["ingredients"], list):
            for ing in recipe["ingredients"]:
                name = ing.get("name") or ing.get("ingredient") or "Unknown"
                measure = ing.get("amount") or ing.get("measure") or ""
                final_ingredients.append({"ingredient": name, "measure": measure})

        return {
            "id": str(r_id),
            "name": recipe.get("name"),
            "category": recipe.get("category") or "Unknown",
            "area": recipe.get("area") or "Unknown",
            "instructions": recipe.get("instructions") or "",
            "image": recipe.get("image"),
            "tags": recipe.get("tags") or "",
            "youtube": recipe.get("youtube") or "",
            "ingredients": final_ingredients
        }

    # --- Methods for Metadata ---
    
    def get_all_categories(self) -> List[str]:
        response = self._make_request("categories")
        if isinstance(response, dict): return response.get("categories", [])
        return response or []

    def get_all_areas(self) -> List[str]:
        response = self._make_request("areas")
        if isinstance(response, dict): return response.get("areas", [])
        return response or []

    def filter_by_category(self, category: str) -> List[Dict[str, Any]]:
        params = {"category": category}
        results = self._make_request("search", params=params)
        if results and isinstance(results, list): return [self.format_recipe(r) for r in results]
        return []

    def filter_by_area(self, area: str) -> List[Dict[str, Any]]:
        params = {"area": area}
        results = self._make_request("search", params=params)
        if results and isinstance(results, list): return [self.format_recipe(r) for r in results]
        return []
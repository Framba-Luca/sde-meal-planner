"""
Recipes Fetch Service - Fetches recipes from TheMealDB API
"""
from typing import Dict, Any, List, Optional
import requests
import redis
import json
import os

# TheMealDB API base URL
THEMEALDB_API_URL = "https://www.themealdb.com/api/json/v1/1"
REDIS_HOST: str = os.getenv("REDIS_HOST", "redis")
REDIS_PORT: int = os.getenv("REDIS_PORT", 6379)

class RecipesFetchService:
    """Service for fetching recipes from TheMealDB"""
    
    def __init__(self):
        self.api_url = THEMEALDB_API_URL
        self.cache = redis.Redis(
            host=os.getenv("REDIS_HOST", "redis"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            decode_responses=True)
    def _make_request(self, endpoint: str) -> Optional[Dict[str, Any]]:
    
        """Make a request to TheMealDB API"""
        try:
            response = requests.get(f"{self.api_url}/{endpoint}")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error making request to TheMealDB: {e}")
            return None
    
    def search_by_name(self, name: str) -> Optional[List[Dict[str, Any]]]:
        """Search for recipes by name"""
        cache_key = f"search:name:{name.lower()}"
        cached = self.cache.get(cache_key)
        if cached:
            return json.loads(cached)

        result = self._make_request(f"search.php?f={name}")
        data = result.get("meals") if result else None
        
        if data:
            self.cache.setex(cache_key, 3600, json.dumps(data))
            
        return data
        
    def search_by_first_letter(self, letter: str) -> Optional[List[Dict[str, Any]]]:
        """Search for recipes by first letter"""
        result = self._make_request(f"lookup.php?i={letter}")
        return result["meals"][0] if result and result.get("meals") else None
    
    def lookup_by_id(self, meal_id: Any) -> Optional[Dict[str, Any]]:
        """Lookup a recipe by ID"""
        cache_key = f"recipe:external:{meal_id}"
        cached = self.cache.get(cache_key)
        if cached:
            return json.loads(cached)
        
        result = self._make_request(f"lookup.php?i={meal_id}")
        if result and result.get("meals"):
            recipe = result["meals"][0]
            # 3. Salva in Redis (es. scadenza 24h)
            self.cache.setex(cache_key, 86400, json.dumps(recipe))
            return recipe
        return None
    
    def lookup_random(self) -> Optional[Dict[str, Any]]:
        """Lookup a random recipe"""
        result = self._make_request("random.php")
        return result["meals"][0] if result and result.get("meals") else None
    
    def list_all_categories(self) -> Optional[List[Dict[str, Any]]]:
        """List all meal categories"""
        result = self._make_request("categories.php")
        return result.get("categories") if result else None
    
    def list_all_areas(self) -> Optional[List[Dict[str, Any]]]:
        """List all meal areas (cuisines)"""
        result = self._make_request("list.php?a=list")
        return result.get("meals") if result else None
    
    def list_all_ingredients(self) -> Optional[List[Dict[str, Any]]]:
        """List all ingredients"""
        result = self._make_request("list.php?i=list")
        return result.get("meals") if result else None

    def filter_by_category(self, category: str) -> Optional[List[Dict[str, Any]]]:
        """Filter recipes by category"""
        result = self._make_request(f"filter.php?c={category}")
        return result.get("meals") if result else None
    
    def filter_by_area(self, area: str) -> Optional[List[Dict[str, Any]]]:
        """Filter recipes by area (cuisine)"""
        result = self._make_request(f"filter.php?a={area}")
        return result.get("meals") if result else None
    
    def filter_by_ingredient(self, ingredient: str) -> Optional[List[Dict[str, Any]]]:
        """Filter recipes by ingredient"""
        result = self._make_request(f"filter.php?i={ingredient}")
        return result.get("meals") if result else None
    
    def parse_recipe_ingredients(self, recipe: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Parse ingredients and measures from a recipe
        
        Args:
            recipe: Recipe dictionary from TheMealDB
            
        Returns:
            List of dictionaries with 'ingredient' and 'measure' keys
        """
        ingredients = []
        for i in range(1, 21):
            ing = (recipe.get(f"strIngredient{i}") or "").strip()
            meas = (recipe.get(f"strMeasure{i}") or "").strip()
            if ing:
                ingredients.append({"ingredient": ing, "measure": meas})
        return ingredients
    
    def format_recipe(self, recipe: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format a recipe for easier consumption
        
        Args:
            recipe: Recipe dictionary from TheMealDB
            
        Returns:
            Formatted recipe dictionary
        """
        return {
            "name": recipe.get("strMeal"),
            "id_recipe": None,
            "id_external": recipe.get("idMeal"),
            "is_external": True,

            "category": recipe.get("strCategory"),
            "area": recipe.get("strArea"),
            "instructions": recipe.get("strInstructions"),
            "image": recipe.get("strMealThumb"),
            "tags": recipe.get("strTags") or "", 
            "youtube": recipe.get("strYoutube") or "",
            "ingredients": self.parse_recipe_ingredients(recipe)
        }
    
    def get_multiple_random_recipes(self, count: int) -> List[Dict[str, Any]]:
        """
        Get multiple random recipes
        
        Args:
            count: Number of random recipes to fetch
            
        Returns:
            List of formatted recipes
        """
        recipes = []
        for _ in range(count):
            recipe = self.lookup_random()
            if recipe:
                recipes.append(self.format_recipe(recipe))
        return recipes

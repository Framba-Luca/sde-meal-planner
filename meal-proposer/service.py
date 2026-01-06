"""
Meal Proposer Service - Proposes recipes from TheMealDB based on ingredients
"""
from typing import Dict, Any, List, Optional
import requests
import random

# TheMealDB API base URL
THEMEALDB_API_URL = "https://www.themealdb.com/api/json/v1/1"


class MealProposerService:
    """Service for proposing meals from TheMealDB"""
    
    def __init__(self):
        self.api_url = THEMEALDB_API_URL
    
    def _make_request(self, endpoint: str) -> Optional[Dict[str, Any]]:
        """Make a request to TheMealDB API"""
        try:
            response = requests.get(f"{self.api_url}/{endpoint}")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error making request to TheMealDB: {e}")
            return None
    
    def search_by_ingredient(self, ingredient: str) -> Optional[List[Dict[str, Any]]]:
        """Search for recipes by ingredient"""
        result = self._make_request(f"filter.php?i={ingredient}")
        if result and "meals" in result:
            return result["meals"]
        return None
    
    def get_recipe_by_id(self, meal_id: int) -> Optional[Dict[str, Any]]:
        """Get full recipe details by ID"""
        result = self._make_request(f"lookup.php?i={meal_id}")
        if result and "meals" in result and result["meals"]:
            return result["meals"][0]
        return None
    
    def get_random_recipe(self) -> Optional[Dict[str, Any]]:
        """Get a random recipe"""
        result = self._make_request("random.php")
        if result and "meals" in result and result["meals"]:
            return result["meals"][0]
        return None
    
    def search_by_name(self, name: str) -> Optional[List[Dict[str, Any]]]:
        """Search for recipes by name"""
        result = self._make_request(f"search.php?s={name}")
        if result and "meals" in result:
            return result["meals"]
        return None
    
    def get_all_categories(self) -> Optional[List[Dict[str, Any]]]:
        """Get all meal categories"""
        result = self._make_request("categories.php")
        if result and "categories" in result:
            return result["categories"]
        return None
    
    def filter_by_category(self, category: str) -> Optional[List[Dict[str, Any]]]:
        """Filter recipes by category"""
        result = self._make_request(f"filter.php?c={category}")
        if result and "meals" in result:
            return result["meals"]
        return None
    
    def get_all_areas(self) -> Optional[List[Dict[str, Any]]]:
        """Get all meal areas (cuisines)"""
        result = self._make_request("list.php?a=list")
        if result and "meals" in result:
            return result["meals"]
        return None
    
    def filter_by_area(self, area: str) -> Optional[List[Dict[str, Any]]]:
        """Filter recipes by area (cuisine)"""
        result = self._make_request(f"filter.php?a={area}")
        if result and "meals" in result:
            return result["meals"]
        return None
    
    def propose_meal(self, ingredient: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Propose a meal based on an ingredient or randomly
        
        Args:
            ingredient: Optional ingredient to filter by
            
        Returns:
            Full recipe details or None if not found
        """
        if ingredient:
            # Search by ingredient
            meals = self.search_by_ingredient(ingredient)
            if meals and len(meals) > 0:
                # Get a random meal from the results
                selected_meal = random.choice(meals)
                # Get full details
                return self.get_recipe_by_id(selected_meal["idMeal"])
            return None
        else:
            # Return a random recipe
            return self.get_random_recipe()
    
    def propose_multiple_meals(self, count: int, ingredient: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Propose multiple meals
        
        Args:
            count: Number of meals to propose
            ingredient: Optional ingredient to filter by
            
        Returns:
            List of full recipe details
        """
        meals = []
        
        if ingredient:
            # Search by ingredient
            meal_list = self.search_by_ingredient(ingredient)
            if meal_list:
                # Shuffle and take first 'count' meals
                random.shuffle(meal_list)
                for meal in meal_list[:count]:
                    full_recipe = self.get_recipe_by_id(meal["idMeal"])
                    if full_recipe:
                        meals.append(full_recipe)
        else:
            # Get random recipes
            for _ in range(count):
                meal = self.get_random_recipe()
                if meal:
                    meals.append(meal)
        
        return meals
    
    def parse_recipe_ingredients(self, recipe: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Parse ingredients and measures from a recipe
        
        Args:
            recipe: Recipe dictionary from TheMealDB
            
        Returns:
            List of dictionaries with 'ingredient' and 'measure' keys
        """
        ingredients = []
        
        for i in range(1, 21):  # TheMealDB supports up to 20 ingredients
            ingredient_key = f"strIngredient{i}"
            measure_key = f"strMeasure{i}"
            
            ingredient = recipe.get(ingredient_key, "").strip()
            measure = recipe.get(measure_key, "").strip()
            
            if ingredient:
                ingredients.append({
                    "ingredient": ingredient,
                    "measure": measure
                })
        
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
            "id": recipe.get("idMeal"),
            "name": recipe.get("strMeal"),
            "category": recipe.get("strCategory"),
            "area": recipe.get("strArea"),
            "instructions": recipe.get("strInstructions"),
            "image": recipe.get("strMealThumb"),
            "tags": recipe.get("strTags", ""),
            "youtube": recipe.get("strYoutube", ""),
            "ingredients": self.parse_recipe_ingredients(recipe)
        }

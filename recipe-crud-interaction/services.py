"""
Recipe CRUD Interaction Service - Manages custom recipes using database service
"""
from typing import Dict, Any, List, Optional
import requests
import os

# Service URLs
DATABASE_SERVICE_URL = os.getenv("DATABASE_SERVICE_URL", "http://database-service:8002")


class RecipeCRUDService:
    """Service for CRUD operations on custom recipes"""
    
    def __init__(self):
        self.database_service_url = DATABASE_SERVICE_URL
    
    def _make_request(self, url: str, method: str = "GET", data: Optional[Dict] = None) -> Optional[Dict[str, Any]]:
        """Make an HTTP request to the database service"""
        try:
            if method == "GET":
                response = requests.get(url)
            elif method == "POST":
                response = requests.post(url, json=data)
            elif method == "PUT":
                response = requests.put(url, json=data)
            elif method == "DELETE":
                response = requests.delete(url)
            else:
                return None
            
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error making request to {url}: {e}")
            return None
    
    def create_custom_recipe(self, user_id: int, recipe_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Create a new custom recipe
        
        Args:
            user_id: ID of the user creating the recipe
            recipe_data: Dictionary containing recipe details
            
        Returns:
            Created recipe or None if failed
        """
        url = f"{self.database_service_url}/custom-recipes"
        data = {
            "user_id": user_id,
            **recipe_data
        }
        
        result = self._make_request(url, method="POST", data=data)
        return result
    
    def get_custom_recipe(self, recipe_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a custom recipe by ID
        
        Args:
            recipe_id: ID of the recipe
            
        Returns:
            Recipe details or None if not found
        """
        url = f"{self.database_service_url}/custom-recipes/{recipe_id}"
        result = self._make_request(url, method="GET")
        return result
    
    def get_user_custom_recipes(self, user_id: int) -> Optional[List[Dict[str, Any]]]:
        """
        Get all custom recipes for a user
        
        Args:
            user_id: ID of the user
            
        Returns:
            List of recipes or None if failed
        """
        url = f"{self.database_service_url}/custom-recipes/user/{user_id}"
        result = self._make_request(url, method="GET")
        return result
    
    def update_custom_recipe(self, recipe_id: int, recipe_data: Dict[str, Any]) -> bool:
        """
        Update a custom recipe
        
        Args:
            recipe_id: ID of the recipe to update
            recipe_data: Dictionary containing updated recipe details
            
        Returns:
            True if successful, False otherwise
        """
        url = f"{self.database_service_url}/custom-recipes/{recipe_id}"
        result = self._make_request(url, method="PUT", data=recipe_data)
        return result is not None
    
    def delete_custom_recipe(self, recipe_id: int) -> bool:
        """
        Delete a custom recipe
        
        Args:
            recipe_id: ID of the recipe to delete
            
        Returns:
            True if successful, False otherwise
        """
        url = f"{self.database_service_url}/custom-recipes/{recipe_id}"
        result = self._make_request(url, method="DELETE")
        return result is not None
    
    def search_custom_recipes(self, user_id: int, search_term: str) -> List[Dict[str, Any]]:
        """
        Search custom recipes by name or category
        
        Args:
            user_id: ID of the user
            search_term: Term to search for in recipe names or categories
            
        Returns:
            List of matching recipes
        """
        recipes = self.get_user_custom_recipes(user_id)
        if not recipes:
            return []
        
        search_term_lower = search_term.lower()
        matching_recipes = []
        
        for recipe in recipes:
            name = recipe.get("name", "").lower()
            category = recipe.get("category", "").lower()
            area = recipe.get("area", "").lower()
            
            if (search_term_lower in name or 
                search_term_lower in category or 
                search_term_lower in area):
                matching_recipes.append(recipe)
        
        return matching_recipes
    
    def get_custom_recipes_by_category(self, user_id: int, category: str) -> List[Dict[str, Any]]:
        """
        Get custom recipes by category
        
        Args:
            user_id: ID of the user
            category: Category to filter by
            
        Returns:
            List of recipes in the category
        """
        recipes = self.get_user_custom_recipes(user_id)
        if not recipes:
            return []
        
        category_lower = category.lower()
        matching_recipes = [
            recipe for recipe in recipes 
            if recipe.get("category", "").lower() == category_lower
        ]
        
        return matching_recipes
    
    def get_custom_recipes_by_area(self, user_id: int, area: str) -> List[Dict[str, Any]]:
        """
        Get custom recipes by area (cuisine)
        
        Args:
            user_id: ID of the user
            area: Area to filter by
            
        Returns:
            List of recipes from the area
        """
        recipes = self.get_user_custom_recipes(user_id)
        if not recipes:
            return []
        
        area_lower = area.lower()
        matching_recipes = [
            recipe for recipe in recipes 
            if recipe.get("area", "").lower() == area_lower
        ]
        
        return matching_recipes
    
    def validate_recipe_data(self, recipe_data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validate recipe data before creation/update
        
        Args:
            recipe_data: Dictionary containing recipe details
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not recipe_data.get("name"):
            return False, "Recipe name is required"
        
        if len(recipe_data.get("name", "")) > 255:
            return False, "Recipe name must be less than 255 characters"
        
        if recipe_data.get("category") and len(recipe_data["category"]) > 100:
            return False, "Category must be less than 100 characters"
        
        if recipe_data.get("area") and len(recipe_data["area"]) > 100:
            return False, "Area must be less than 100 characters"
        
        return True, None

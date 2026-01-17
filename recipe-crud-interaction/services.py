"""
Recipe CRUD Interaction Service - Manages custom recipes using database service
"""
from typing import Dict, Any, List, Optional
import requests
import os

# Service URLs
DATABASE_SERVICE_URL = os.getenv("DATABASE_SERVICE_URL", "http://database-service:8002")
RECIPES_FETCH_SERVICE_URL = os.getenv("RECIPES_FETCH_SERVICE_URL", "http://recipes-fetch-service:8006")
INTERNAL_SERVICE_SECRET = os.getenv("INTERNAL_SERVICE_SECRET", "internal-service-secret-key")

class RecipeCRUDService:
    """Service for CRUD operations on custom recipes"""
    
    def __init__(self):
        self.database_service_url = DATABASE_SERVICE_URL
        self.internal_service_secret = INTERNAL_SERVICE_SECRET
        self.fetch_service_url = RECIPES_FETCH_SERVICE_URL
    
    def _make_request(self, url: str, method: str = "GET", data: Optional[Dict] = None) -> Optional[Dict[str, Any]]:
        """Make an HTTP request to the database service"""
        headers = {
            "Authorization": f"Bearer {self.internal_service_secret}"
        }
        
        try:
            if method == "GET":
                response = requests.get(url, headers=headers)
            elif method == "POST":
                response = requests.post(url, json=data, headers=headers)
            elif method == "PUT":
                response = requests.put(url, json=data, headers=headers)
            elif method == "DELETE":
                response = requests.delete(url, headers=headers)
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
        url = f"{self.database_service_url}/api/v1/recipes"
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
        url = f"{self.database_service_url}/api/v1/recipes/{recipe_id}"
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
        url = f"{self.database_service_url}/api/v1/recipes/user/{user_id}"
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
        url = f"{self.database_service_url}/api/v1/recipes/{recipe_id}"
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
        url = f"{self.database_service_url}/api/v1/recipes/{recipe_id}"
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
    
    # ==========================================
    # NUOVI METODI PER LOGICA SHADOW & REVIEWS
    # ==========================================

    def ensure_shadow_recipe(self, external_id: str) -> Optional[int]:
        """
        Garantisce che una ricetta esterna esista nel DB locale.
        1. Cerca nel DB.
        2. Se manca, scarica dal Fetch Service (8006).
        3. Crea la 'Shadow Recipe' nel DB (8002).
        Returns: L'ID interno del database.
        """
        # 1. Controlla se esiste già nel Database Service
        # Endpoint definito nel DB service: @router.get("/external/{external_id}")
        check_url = f"{self.database_service_url}/api/v1/recipes/external/{external_id}"
        existing_recipe = self._make_request(check_url, method="GET")
        
        if existing_recipe and existing_recipe.get('id'):
            return existing_recipe['id']

        print(f"Shadow Recipe not found locally. Fetching external ID: {external_id}...")

        # 2. Se non esiste, recupera i dettagli dal Recipes Fetch Service (Port 8006)
        # Nota: Qui usiamo requests diretto perché il fetch service è interno/pubblico
        fetch_url = f"{self.fetch_service_url}/recipe/{external_id}"
        try:
            resp = requests.get(fetch_url)
            if resp.status_code == 404:
                print(f"Recipe {external_id} not found in Fetch Service")
                return None
            resp.raise_for_status()
            meal_data = resp.json()
        except Exception as e:
            print(f"Error calling fetch service: {e}")
            return None

        # 3. Prepara i dati per la creazione della Shadow Recipe
        # Mappiamo i campi del Fetch Service su quelli del Database Service
        shadow_payload = {
            "name": meal_data.get('name'),
            "image": meal_data.get('image'),
            "external_id": str(meal_data.get('id')),
            "category": meal_data.get('category'),
            "area": meal_data.get('area')
            # is_custom sarà settato a FALSE dal DB service automaticamente
        }

        # 4. Crea la ricetta nel Database Service
        create_url = f"{self.database_service_url}/api/v1/recipes/shadow"
        new_recipe = self._make_request(create_url, method="POST", data=shadow_payload)
        
        return new_recipe['id'] if new_recipe else None

    def create_review(self, user_id: int, review_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Gestisce la creazione della recensione gestendo la complessità ibrida.
        """
        recipe_id = review_data.get('recipe_id')
        external_id = review_data.get('external_id')

        # CASO A: Ricetta Esterna (TheMealDB)
        if not recipe_id and external_id:
            # Qui avviene la magia: importiamo la ricetta al volo
            recipe_id = self.ensure_shadow_recipe(external_id)
        
        if not recipe_id:
            return {"error": "Impossibile trovare o importare la ricetta richiesta"}

        # Ora abbiamo sicuramente un ID interno. Inviamo la review al DB.
        review_payload = {
            "user_id": user_id,
            "recipe_id": recipe_id, 
            "rating": review_data['rating'],
            "comment": review_data['comment']
        }
        
        url = f"{self.database_service_url}/api/v1/reviews/"
        result = self._make_request(url, method="POST", data=review_payload)
        
        if result:
            return result
        else:
            return {"error": "Errore durante il salvataggio della recensione nel Database"}

    def get_reviews(self, recipe_id: int) -> List[Dict]:
        """Ottiene le recensioni dato un ID interno"""
        url = f"{self.database_service_url}/api/v1/reviews/recipe/{recipe_id}"
        result = self._make_request(url, method="GET")
        return result if result is not None else []

"""
Meal Planner Service - Creates meal plans using the meal proposer service
"""
from typing import Dict, Any, List, Optional
from datetime import date, timedelta
import requests
import os

# Service URLs
MEAL_PROPOSER_URL = os.getenv("MEAL_PROPOSER_URL", "http://meal-proposer:8003")
DATABASE_SERVICE_URL = os.getenv("DATABASE_SERVICE_URL", "http://database-service:8002")
INTERNAL_SERVICE_SECRET = os.getenv("INTERNAL_SERVICE_SECRET", "internal-service-secret-key")


class MealPlannerService:
    """Service for creating and managing meal plans"""
    
    def __init__(self):
        self.meal_proposer_url = MEAL_PROPOSER_URL
        self.database_service_url = DATABASE_SERVICE_URL
    
    def _make_request(self, url: str, method: str = "GET", data: Optional[Dict] = None, headers: Optional[Dict] = None) -> Optional[Dict[str, Any]]:
        """Make an HTTP request to another service"""
        try:
            # Add internal service authentication header
            if headers is None:
                headers = {}
            headers["Authorization"] = f"Bearer {INTERNAL_SERVICE_SECRET}"
            
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
    
    def propose_meal(self, ingredient: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Propose a single meal using the meal proposer service
        
        Args:
            ingredient: Optional ingredient to filter by
            
        Returns:
            Recipe details or None if not found
        """
        url = f"{self.meal_proposer_url}/propose"
        data = {"ingredient": ingredient} if ingredient else {}
        
        result = self._make_request(url, method="POST", data=data)
        return result
    
    def create_meal_plan(self, user_id: int, start_date: date, end_date: date) -> Optional[Dict[str, Any]]:
        """
        Create a meal plan in the database
        
        Args:
            user_id: ID of the user
            start_date: Start date of the meal plan
            end_date: End date of the meal plan
            
        Returns:
            Created meal plan or None if failed
        """
        url = f"{self.database_service_url}/api/v1/meal-plans/"
        data = {
            "user_id": user_id,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        }
        
        result = self._make_request(url, method="POST", data=data)
        return result
    
    def add_meal_to_plan(self, meal_plan_id: int, mealdb_id: int, meal_date: date, meal_type: str) -> Optional[Dict[str, Any]]:
        """
        Add a meal to a meal plan
        
        Args:
            meal_plan_id: ID of the meal plan
            mealdb_id: ID of the recipe from TheMealDB
            meal_date: Date of the meal
            meal_type: Type of meal (breakfast, lunch, dinner)
            
        Returns:
            Created meal plan item or None if failed
        """
        url = f"{self.database_service_url}/api/v1/meal-plans/items/"
        data = {
            "meal_plan_id": meal_plan_id,
            "mealdb_id": mealdb_id,
            "meal_date": meal_date.isoformat(),
            "meal_type": meal_type
        }
        
        result = self._make_request(url, method="POST", data=data)
        return result
    
    def generate_meal_plan(self, user_id: int, num_days: int, start_date: Optional[date] = None, ingredient: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Generate a complete meal plan for a specified number of days
        
        Args:
            user_id: ID of the user
            num_days: Number of days to plan for
            start_date: Start date of the meal plan (defaults to today)
            ingredient: Optional ingredient to filter recipes by
            
        Returns:
            Generated meal plan with meals for each day
        """
        if start_date is None:
            start_date = date.today()
        
        end_date = start_date + timedelta(days=num_days - 1)
        
        # Create meal plan in database
        meal_plan = self.create_meal_plan(user_id, start_date, end_date)
        if not meal_plan:
            return None
        
        meal_plan_id = meal_plan["id"]
        meal_types = ["breakfast", "lunch", "dinner"]
        days_meals = {}
        
        # Generate meals for each day
        for day_offset in range(num_days):
            current_date = start_date + timedelta(days=day_offset)
            day_meals = {}
            
            for meal_type in meal_types:
                # Propose a meal for this meal type
                meal = self.propose_meal(ingredient)
                if meal:
                    # Add meal to plan
                    meal_item = self.add_meal_to_plan(
                        meal_plan_id=meal_plan_id,
                        mealdb_id=meal["id"],
                        meal_date=current_date,
                        meal_type=meal_type
                    )
                    
                    day_meals[meal_type] = {
                        "recipe": meal,
                        "meal_plan_item_id": meal_item["id"] if meal_item else None
                    }
            
            days_meals[current_date.isoformat()] = day_meals
        
        return {
            "meal_plan_id": meal_plan_id,
            "user_id": user_id,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "days": days_meals
        }
    
    def get_meal_plan(self, meal_plan_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a meal plan by ID
        
        Args:
            meal_plan_id: ID of the meal plan
            
        Returns:
            Meal plan details or None if not found
        """
        url = f"{self.database_service_url}/api/v1/meal-plans/{meal_plan_id}"
        result = self._make_request(url, method="GET")
        return result
    
    def get_meal_plan_items(self, meal_plan_id: int) -> Optional[List[Dict[str, Any]]]:
        """
        Get all items in a meal plan
        
        Args:
            meal_plan_id: ID of the meal plan
            
        Returns:
            List of meal plan items or None if failed
        """
        url = f"{self.database_service_url}/api/v1/meal-plans/items/{meal_plan_id}"
        result = self._make_request(url, method="GET")
        return result
    
    def get_user_meal_plans(self, user_id: int) -> Optional[List[Dict[str, Any]]]:
        """
        Get all meal plans for a user
        
        Args:
            user_id: ID of the user
            
        Returns:
            List of meal plans or None if failed
        """
        url = f"{self.database_service_url}/api/v1/meal-plans/user/{user_id}"
        result = self._make_request(url, method="GET")
        return result
    
    def delete_meal_plan(self, meal_plan_id: int) -> bool:
        """
        Delete a meal plan
        
        Args:
            meal_plan_id: ID of the meal plan
            
        Returns:
            True if successful, False otherwise
        """
        url = f"{self.database_service_url}/api/v1/meal-plans/{meal_plan_id}"
        result = self._make_request(url, method="DELETE")
        return result is not None
    
    def update_meal_in_plan(self, item_id: int, mealdb_id: Optional[int] = None, meal_type: Optional[str] = None) -> bool:
        """
        Update a meal in a meal plan
        
        Args:
            item_id: ID of the meal plan item
            mealdb_id: New recipe ID (optional)
            meal_type: New meal type (optional)
            
        Returns:
            True if successful, False otherwise
        """
        url = f"{self.database_service_url}/api/v1/meal-plans/items/{item_id}"
        data = {}
        if mealdb_id is not None:
            data["mealdb_id"] = mealdb_id
        if meal_type is not None:
            data["meal_type"] = meal_type
        
        if not data:
            return False
        
        result = self._make_request(url, method="PUT", data=data)
        return result is not None
    
    def delete_meal_from_plan(self, item_id: int) -> bool:
        """
        Delete a meal from a meal plan
        
        Args:
            item_id: ID of the meal plan item
            
        Returns:
            True if successful, False otherwise
        """
        url = f"{self.database_service_url}/api/v1/meal-plans/items/{item_id}"
        result = self._make_request(url, method="DELETE")
        return result is not None
    
    def get_full_meal_plan(self, meal_plan_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a full meal plan with all recipe details
        
        Args:
            meal_plan_id: ID of the meal plan
            
        Returns:
            Full meal plan with recipe details or None if failed
        """
        # Get meal plan details
        meal_plan = self.get_meal_plan(meal_plan_id)
        if not meal_plan:
            return None
        
        # Get meal plan items
        items = self.get_meal_plan_items(meal_plan_id)
        if not items:
            return None
        
        # Group items by date and meal type
        days_meals = {}
        for item in items:
            meal_date = item["meal_date"]
            meal_type = item["meal_type"]
            
            if meal_date not in days_meals:
                days_meals[meal_date] = {}
            
            # Fetch recipe details from meal proposer service
            recipe = self._get_recipe_details(item["mealdb_id"])
            if recipe:
                days_meals[meal_date][meal_type] = {
                    "recipe": recipe,
                    "meal_plan_item_id": item["id"]
                }
        
        return {
            "meal_plan_id": meal_plan_id,
            "user_id": meal_plan["user_id"],
            "start_date": meal_plan["start_date"],
            "end_date": meal_plan["end_date"],
            "days": days_meals
        }
    
    def _get_recipe_details(self, mealdb_id: int) -> Optional[Dict[str, Any]]:
        """
        Get recipe details from meal proposer service
        
        Args:
            mealdb_id: ID of the recipe from TheMealDB
            
        Returns:
            Recipe details or None if failed
        """
        url = f"{self.meal_proposer_url}/recipe/{mealdb_id}"
        result = self._make_request(url, method="GET")
        return result

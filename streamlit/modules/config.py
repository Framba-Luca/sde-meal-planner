import os

# Service URLs
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://authentication-service:8001")
DATABASE_SERVICE_URL = os.getenv("DATABASE_SERVICE_URL", "http://database-service:8002")
MEAL_PROPOSER_URL = os.getenv("MEAL_PROPOSER_URL", "http://meal-proposer:8003")
MEAL_PLANNER_URL = os.getenv("MEAL_PLANNER_URL", "http://meal-planner-pcl:8004")
RECIPE_CRUD_URL = os.getenv("RECIPE_CRUD_URL", "http://recipe-crud-interaction:8005")
RECIPES_FETCH_URL = os.getenv("RECIPES_FETCH_URL", "http://recipes-fetch-service:8006")

API_VERSION = os.getenv("API_VERSION", "api/v1")
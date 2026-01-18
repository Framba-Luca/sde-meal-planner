import os

class Settings:
    PROJECT_NAME: str = "Recipe CRUD Interaction Service"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # URLs
    DATABASE_SERVICE_URL: str = os.getenv("DATABASE_SERVICE_URL", "http://database-service:8002")
    RECIPES_FETCH_SERVICE_URL: str = os.getenv("RECIPES_FETCH_SERVICE_URL", "http://recipes-fetch-service:8006")
    INTERNAL_SERVICE_SECRET: str = os.getenv("INTERNAL_SERVICE_SECRET", "internal-service-secret-key")

settings = Settings()
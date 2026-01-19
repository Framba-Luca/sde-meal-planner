import os

class Settings:
    PROJECT_NAME: str = "Recipe CRUD Interaction Service"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    DATABASE_SERVICE_URL: str = os.getenv("DATABASE_SERVICE_URL", "http://database-service:8002")
    AUTHENTICATION_SERVICE_URL: str = os.getenv("AUTHENTICATION_SERVICE_URL", "http://authentication-service:8001")
    RECIPES_FETCH_SERVICE_URL: str = os.getenv("RECIPES_FETCH_SERVICE_URL", "http://recipes-fetch-service:8006")
    
    INTERNAL_SERVICE_SECRET: str = os.getenv("INTERNAL_SERVICE_SECRET", "my-super-secret-internal-key")

settings = Settings()
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Database Service"
    API_V1_STR: str = "/api/v1"
    
    # --- Security & Auth ---
    SECRET_KEY: str = "la-tua-chiave-super-segreta-e-lunghissima"
    ALGORITHM: str = "HS256"
    
    # --- Database (Postgres) ---
    DB_HOST: str = "postgres"
    DB_PORT: str = "5432"
    DB_NAME: str = "mealplanner"
    DB_USER: str = "mealplanner"
    DB_PASSWORD: str = "mealplanner"
    
    # --- Cache (Redis) ---
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
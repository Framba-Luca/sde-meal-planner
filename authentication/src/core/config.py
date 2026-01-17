import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Meta Info
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Authentication Service"
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # External Services
    DATABASE_SERVICE_URL: str = os.getenv("DATABASE_SERVICE_URL", "http://database-service:8002")
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:8501")
    
    # Google OAuth
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
    GOOGLE_REDIRECT_URI: str = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8001/auth/google/callback")

    # Redois Configuration
    REDIS_HOST: str = os.getenv("REDIS_HOST", "redis")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", 6379))

    class Config:
        # Pydantic cercherà un file .env automaticamente
        env_file = ".env"
        case_sensitive = True

# Istanza singleton da importare ovunque
settings = Settings()
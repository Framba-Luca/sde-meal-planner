from fastapi import FastAPI
from contextlib import asynccontextmanager
import sys
import os

# Ensure Python can see the src modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.config import settings
from src.core.database import init_db
from src.api.v1.router import api_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages the application lifecycle.
    """
    # --- STARTUP PHASE ---
    print(f"Starting {settings.PROJECT_NAME}...")

    # Automatically create tables based on the imported models
    print("Initializing database (creating tables)...")
    init_db()

    yield  # The application is running

    # --- SHUTDOWN PHASE ---
    print(f"Shutting down {settings.PROJECT_NAME}...")
    # With SQLModel/SQLAlchemy engine, it is not strictly necessary
    # to explicitly close connections here; the engine manages the pool.

# --- App Definition ---
app = FastAPI(
    title=settings.PROJECT_NAME,
    version="2.0.0",
    description="Database microservice using SQLModel.",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# --- Include Routers ---
app.include_router(api_router, prefix=settings.API_V1_STR)

# --- Health Check ---
@app.get("/health")
def health_check():
    return {"status": "ok", "db_engine": "SQLModel"}

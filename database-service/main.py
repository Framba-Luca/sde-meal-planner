from fastapi import FastAPI
from contextlib import asynccontextmanager
import uvicorn
import sys
import os

# Assicuriamoci che python veda i moduli src
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.config import settings
from src.core.database import db_adapter
from src.api.v1.router import api_router

# --- Schema Initialization Queries ---
# Definiamo qui le query per creare le tabelle al primo avvio.
# In produzione useresti Alembic, ma questo è perfetto per ora.
SCHEMA_QUERIES = [
    """
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username VARCHAR(50) UNIQUE NOT NULL,
        hashed_password VARCHAR(255) NOT NULL,
        email VARCHAR(100),
        full_name VARCHAR(100),
        created_at TIMESTAMP DEFAULT NOW(),
        disabled BOOLEAN DEFAULT FALSE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS meal_plans (
        id SERIAL PRIMARY KEY,
        user_id INT REFERENCES users(id) ON DELETE CASCADE,
        start_date DATE NOT NULL,
        end_date DATE NOT NULL,
        created_at TIMESTAMP DEFAULT NOW()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS meal_plan_items (
        id SERIAL PRIMARY KEY,
        meal_plan_id INT REFERENCES meal_plans(id) ON DELETE CASCADE,
        mealdb_id INT NOT NULL,
        meal_date DATE NOT NULL,
        meal_type VARCHAR(20) NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS custom_recipes (
        id SERIAL PRIMARY KEY,
        user_id INT REFERENCES users(id) ON DELETE CASCADE,
        name VARCHAR(255) NOT NULL,
        category VARCHAR(100),
        area VARCHAR(100),
        instructions TEXT,
        image TEXT,
        tags TEXT,
        created_at TIMESTAMP DEFAULT NOW()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS custom_recipe_ingredients (
        id SERIAL PRIMARY KEY,
        recipe_id INT REFERENCES custom_recipes(id) ON DELETE CASCADE,
        ingredient_name VARCHAR(255) NOT NULL,
        measure VARCHAR(100)
    )
    """
]

def init_tables():
    """Esegue le query di creazione tabelle all'avvio."""
    print("Checking database tables...")
    try:
        with db_adapter.get_cursor() as cur:
            for query in SCHEMA_QUERIES:
                cur.execute(query)
            
            # Migration: Add missing columns if they don't exist
            # This handles cases where tables were created with older schemas
            migration_queries = [
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS hashed_password VARCHAR(255)",
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS email VARCHAR(100)",
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS disabled BOOLEAN DEFAULT FALSE"
            ]
            for query in migration_queries:
                try:
                    cur.execute(query)
                except Exception as e:
                    # Column might already exist or other issue, log but continue
                    print(f"Migration query note: {e}")
                    
        print("Database tables initialized successfully.")
    except Exception as e:
        print(f"Error initializing tables: {e}")
        # Non rilanciamo l'eccezione per non crashare se il DB è temporaneamente down,
        # ma in produzione dovresti gestire retry o crashare.

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gestisce il ciclo di vita dell'applicazione (Startup & Shutdown).
    Sostituisce i vecchi eventi @app.on_event("startup").
    """
    # --- STARTUP PHASE ---
    print(f"Starting {settings.PROJECT_NAME}...")
    try:
        db_adapter.connect()
        init_tables()
    except Exception as e:
        print(f"CRITICAL: Failed to connect to database at startup: {e}")
    
    yield  # Qui l'applicazione gira e serve le richieste
    
    # --- SHUTDOWN PHASE ---
    print(f"Shutting down {settings.PROJECT_NAME}...")
    try:
        db_adapter.disconnect()
    except Exception as e:
        print(f"Error disconnecting database: {e}")

# --- App Definition ---
app = FastAPI(
    title=settings.PROJECT_NAME,
    version="2.0.0",
    description="Microservizio Database con gestione integrata di Redis per la sicurezza.",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# --- Include Routers ---
# Colleghiamo il router centrale che contiene users, meals, recipes, security
app.include_router(api_router, prefix=settings.API_V1_STR)

# --- Health Check ---
@app.get("/health")
def health_check():
    """Simple health check for Docker/K8s"""
    return {"status": "healthy", "service": settings.PROJECT_NAME}

if __name__ == "__main__":
    # Avvio per debugging locale diretto (python main.py)
    uvicorn.run("main:app", host="0.0.0.0", port=8002, reload=True)
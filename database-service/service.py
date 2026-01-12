"""
Database Service - Adaptive database abstraction layer for PostgreSQL
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Generator
from datetime import date
import os
import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager

# Database configuration
DB_HOST = os.getenv("DB_HOST", "postgres")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "mealplanner")
DB_USER = os.getenv("DB_USER", "mealplanner")
DB_PASSWORD = os.getenv("DB_PASSWORD", "mealplanner")


class DatabaseAdapter(ABC):
    """Abstract base class for database adapters"""
    
    @abstractmethod
    def connect(self):
        """Initialize connection pool"""
        pass
    
    @abstractmethod
    def disconnect(self):
        """Close all connections"""
        pass


class PostgreSQLAdapter(DatabaseAdapter):
    """PostgreSQL implementation with Connection Pooling"""
    
    def __init__(self):
        self._pool = None
    
    def connect(self) -> bool:
        """Initialize PostgreSQL connection pool"""
        try:
            # Create a thread-safe connection pool (min 1, max 20 connections)
            self._pool = psycopg2.pool.ThreadedConnectionPool(
                minconn=1,
                maxconn=20,
                host=DB_HOST,
                port=DB_PORT,
                database=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD,
                cursor_factory=RealDictCursor
            )
            print("Database connection pool created")
            return True
        except Exception as e:
            print(f"Error connecting to database: {e}")
            return False
    
    def disconnect(self):
        """Close all connections in the pool"""
        if self._pool:
            self._pool.closeall()
            print("Database connection pool closed")

    @contextmanager
    def get_cursor(self) -> Generator[Any, None, None]:
        """
        Context manager to get a cursor from the pool.
        Handles commit on success, rollback on error, and releasing connection back to pool.
        """
        if not self._pool:
            success = self.connect()
            if not success:
                raise Exception("Failed to connect to database")
            
        conn = self._pool.getconn()
        try:
            with conn.cursor() as cur:
                yield cur
            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"Transaction error: {e}")
            raise e
        finally:
            self._pool.putconn(conn)


class DatabaseService:
    """Service for database operations using adaptive pattern"""
    
    def __init__(self, adapter: Optional[PostgreSQLAdapter] = None):
        self.adapter = adapter or PostgreSQLAdapter()
        # Connect lazily or on init
        self.adapter.connect()
    
    def close(self):
        """Close database connection pool"""
        self.adapter.disconnect()

    # --- Internal Helpers ---
    def _execute_query(self, query: str, params: tuple = None) -> List[Dict[str, Any]]:
        """Helper to execute SELECT queries safely"""
        with self.adapter.get_cursor() as cur:
            cur.execute(query, params)
            # Fetch results only for SELECT or RETURNING clauses
            if query.strip().upper().startswith("SELECT") or "RETURNING" in query.upper():
                return [dict(row) for row in cur.fetchall()]
            return []

    def _execute_update(self, query: str, params: tuple = None) -> int:
        """Helper to execute INSERT/UPDATE/DELETE queries safely"""
        with self.adapter.get_cursor() as cur:
            cur.execute(query, params)
            return cur.rowcount

    # --- User operations ---
    def create_user(self, username: str, full_name: Optional[str] = None, hashed_password: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Create a new user"""
        query = """
            INSERT INTO users (username, full_name, hashed_password)
            VALUES (%s, %s, %s)
            RETURNING id, username, full_name, created_at::text;
        """
        params = (username, full_name or username, hashed_password)
        rows = self._execute_query(query, params)
        return rows[0] if rows else None
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        query = "SELECT id, username, full_name, created_at FROM users WHERE id = %s"
        rows = self._execute_query(query, (user_id,))
        return rows[0] if rows else None
    
    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user by username (includes hashed_password)"""
        query = "SELECT id, username, full_name, created_at, hashed_password FROM users WHERE username = %s"
        rows = self._execute_query(query, (username,))
        return rows[0] if rows else None
    
    def get_all_users(self) -> List[Dict[str, Any]]:
        """Get all users"""
        query = "SELECT id, username, full_name, created_at FROM users ORDER BY created_at DESC"
        return self._execute_query(query)
    
    def update_user(self, user_id: int, full_name: Optional[str] = None) -> bool:
        """Update user information"""
        if full_name:
            query = "UPDATE users SET full_name = %s WHERE id = %s"
            params = (full_name, user_id)
        else:
            return False
        
        affected = self._execute_update(query, params)
        return affected > 0
    
    def delete_user(self, user_id: int) -> bool:
        """Delete a user"""
        query = "DELETE FROM users WHERE id = %s"
        affected = self._execute_update(query, (user_id,))
        return affected > 0
    
    # --- Meal plan operations ---
    def create_meal_plan(self, user_id: int, start_date: date, end_date: date) -> Optional[Dict[str, Any]]:
        """Create a new meal plan"""
        query = """
            INSERT INTO meal_plans (user_id, start_date, end_date)
            VALUES (%s, %s, %s)
            RETURNING id, user_id, start_date, end_date, created_at
        """
        params = (user_id, start_date, end_date)
        rows = self._execute_query(query, params)
        return rows[0] if rows else None
    
    def get_meal_plan_by_id(self, meal_plan_id: int) -> Optional[Dict[str, Any]]:
        """Get meal plan by ID"""
        query = "SELECT id, user_id, start_date, end_date, created_at FROM meal_plans WHERE id = %s"
        rows = self._execute_query(query, (meal_plan_id,))
        return rows[0] if rows else None
    
    def get_meal_plans_by_user(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all meal plans for a user"""
        query = """
            SELECT id, user_id, start_date, end_date, created_at 
            FROM meal_plans 
            WHERE user_id = %s 
            ORDER BY created_at DESC
        """
        return self._execute_query(query, (user_id,))
    
    def delete_meal_plan(self, meal_plan_id: int) -> bool:
        """Delete a meal plan"""
        query = "DELETE FROM meal_plans WHERE id = %s"
        affected = self._execute_update(query, (meal_plan_id,))
        return affected > 0
    
    # --- Meal plan item operations ---
    def add_meal_plan_item(self, meal_plan_id: int, mealdb_id: int, meal_date: date, meal_type: str) -> Optional[Dict[str, Any]]:
        """Add a meal to a meal plan"""
        query = """
            INSERT INTO meal_plan_items (meal_plan_id, mealdb_id, meal_date, meal_type)
            VALUES (%s, %s, %s, %s)
            RETURNING id, meal_plan_id, mealdb_id, meal_date, meal_type
        """
        params = (meal_plan_id, mealdb_id, meal_date, meal_type)
        rows = self._execute_query(query, params)
        return rows[0] if rows else None
    
    def get_meal_plan_items(self, meal_plan_id: int) -> List[Dict[str, Any]]:
        """Get all items in a meal plan"""
        query = """
            SELECT id, meal_plan_id, mealdb_id, meal_date, meal_type 
            FROM meal_plan_items 
            WHERE meal_plan_id = %s 
            ORDER BY meal_date, meal_type
        """
        return self._execute_query(query, (meal_plan_id,))
    
    def get_meal_plan_items_by_date(self, meal_plan_id: int, meal_date: date) -> List[Dict[str, Any]]:
        """Get meal plan items for a specific date"""
        query = """
            SELECT id, meal_plan_id, mealdb_id, meal_date, meal_type 
            FROM meal_plan_items 
            WHERE meal_plan_id = %s AND meal_date = %s 
            ORDER BY meal_type
        """
        return self._execute_query(query, (meal_plan_id, meal_date))
    
    def update_meal_plan_item(self, item_id: int, mealdb_id: Optional[int] = None, meal_type: Optional[str] = None) -> bool:
        """Update a meal plan item"""
        updates = []
        params = []
        
        # Using %s for standard psycopg2 parameter binding
        if mealdb_id is not None:
            updates.append("mealdb_id = %s")
            params.append(mealdb_id)
        
        if meal_type is not None:
            updates.append("meal_type = %s")
            params.append(meal_type)
        
        if not updates:
            return False
        
        params.append(item_id)
        query = f"UPDATE meal_plan_items SET {', '.join(updates)} WHERE id = %s"
        
        affected = self._execute_update(query, tuple(params))
        return affected > 0
    
    def delete_meal_plan_item(self, item_id: int) -> bool:
        """Delete a meal plan item"""
        query = "DELETE FROM meal_plan_items WHERE id = %s"
        affected = self._execute_update(query, (item_id,))
        return affected > 0
    
    # --- Custom recipe operations ---
    def create_custom_recipe(self, user_id: int, recipe_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a custom recipe"""
        query = """
            INSERT INTO custom_recipes (user_id, name, category, area, instructions, image, tags)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id, user_id, name, category, area, instructions, image, tags, created_at
        """
        params = (
            user_id,
            recipe_data.get("name", ""),
            recipe_data.get("category", ""),
            recipe_data.get("area", ""),
            recipe_data.get("instructions", ""),
            recipe_data.get("image", ""),
            recipe_data.get("tags", "")
        )
        rows = self._execute_query(query, params)
        return rows[0] if rows else None
    
    def get_custom_recipes_by_user(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all custom recipes for a user"""
        query = """
            SELECT id, user_id, name, category, area, instructions, image, tags, created_at 
            FROM custom_recipes 
            WHERE user_id = %s 
            ORDER BY created_at DESC
        """
        return self._execute_query(query, (user_id,))
    
    def get_custom_recipe_by_id(self, recipe_id: int) -> Optional[Dict[str, Any]]:
        """Get custom recipe by ID"""
        query = """
            SELECT id, user_id, name, category, area, instructions, image, tags, created_at 
            FROM custom_recipes 
            WHERE id = %s
        """
        rows = self._execute_query(query, (recipe_id,))
        return rows[0] if rows else None
    
    def update_custom_recipe(self, recipe_id: int, recipe_data: Dict[str, Any]) -> bool:
        """Update a custom recipe"""
        allowed_fields = ["name", "category", "area", "instructions", "image", "tags"]
        updates = []
        params = []
        
        for field in allowed_fields:
            if field in recipe_data:
                updates.append(f"{field} = %s")
                params.append(recipe_data[field])
        
        if not updates:
            return False
        
        params.append(recipe_id)
        query = f"UPDATE custom_recipes SET {', '.join(updates)} WHERE id = %s"
        
        affected = self._execute_update(query, tuple(params))
        return affected > 0
    
    def delete_custom_recipe(self, recipe_id: int) -> bool:
        """Delete a custom recipe"""
        query = "DELETE FROM custom_recipes WHERE id = %s"
        affected = self._execute_update(query, (recipe_id,))
        return affected > 0
    
    # --- Database initialization ---
    def initialize_tables(self) -> bool:
        """Create all necessary tables"""
        schema_queries = [
            """
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    hashed_password VARCHAR(255),
                    email VARCHAR(100),
                    full_name VARCHAR(100),
                    created_at TIMESTAMP DEFAULT NOW()
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
        
        try:
            with self.adapter.get_cursor() as cur:
                for query in schema_queries:
                    cur.execute(query)
            return True
        except Exception as e:
            print(f"Error initializing tables: {e}")
            return False
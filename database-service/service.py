"""
Database Service - Adaptive database abstraction layer for PostgreSQL
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import date
import os
import psycopg2
from psycopg2.extras import RealDictCursor

# Database configuration
DB_HOST = os.getenv("DB_HOST", "postgres")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "mealplanner")
DB_USER = os.getenv("DB_USER", "mealplanner")
DB_PASSWORD = os.getenv("DB_PASSWORD", "mealplanner")


class DatabaseAdapter(ABC):
    """Abstract base class for database adapters"""
    
    @abstractmethod
    def connect(self) -> bool:
        """Establish database connection"""
        pass
    
    @abstractmethod
    def disconnect(self):
        """Close database connection"""
        pass
    
    @abstractmethod
    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """Execute a SELECT query and return results"""
        pass
    
    @abstractmethod
    def execute_update(self, query: str, params: Optional[tuple] = None) -> int:
        """Execute an INSERT/UPDATE/DELETE query and return affected rows"""
        pass
    
    @abstractmethod
    def execute_transaction(self, queries: List[tuple]) -> bool:
        """Execute multiple queries in a transaction"""
        pass


class PostgreSQLAdapter(DatabaseAdapter):
    """PostgreSQL implementation of DatabaseAdapter"""
    
    def __init__(self):
        self.connection = None
        self.cursor = None
    
    def connect(self) -> bool:
        """Establish PostgreSQL connection"""
        try:
            self.connection = psycopg2.connect(
                host=DB_HOST,
                port=DB_PORT,
                database=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD
            )
            self.cursor = self.connection.cursor(cursor_factory=RealDictCursor)
            return True
        except Exception as e:
            print(f"Error connecting to database: {e}")
            return False
    
    def disconnect(self):
        """Close PostgreSQL connection"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
    
    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """Execute a SELECT query and return results"""
        try:
            self.cursor.execute(query, params)
            results = self.cursor.fetchall()
            return [dict(row) for row in results]
        except Exception as e:
            print(f"Error executing query: {e}")
            return []
    
    def execute_update(self, query: str, params: Optional[tuple] = None) -> int:
        """Execute an INSERT/UPDATE/DELETE query and return affected rows"""
        try:
            self.cursor.execute(query, params)
            self.connection.commit()
            return self.cursor.rowcount
        except Exception as e:
            self.connection.rollback()
            print(f"Error executing update: {e}")
            return 0
    
    def execute_transaction(self, queries: List[tuple]) -> bool:
        """Execute multiple queries in a transaction"""
        try:
            for query, params in queries:
                self.cursor.execute(query, params)
            self.connection.commit()
            return True
        except Exception as e:
            self.connection.rollback()
            print(f"Error executing transaction: {e}")
            return False


class DatabaseService:
    """Service for database operations using adaptive pattern"""
    
    def __init__(self, adapter: Optional[DatabaseAdapter] = None):
        self.adapter = adapter or PostgreSQLAdapter()
        self._ensure_connection()
    
    def _ensure_connection(self):
        """Ensure database connection is established"""
        if not self.adapter.connection:
            self.adapter.connect()
    
    def _reconnect_if_needed(self):
        """Reconnect if connection is lost"""
        try:
            self.adapter.connection.ping()
        except:
            self.adapter.connect()
    
    # User operations
    def create_user(self, username: str, full_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Create a new user"""
        query = """
            INSERT INTO users (username, full_name)
            VALUES (%s, %s)
            RETURNING id, username, full_name, created_at
        """
        params = (username, full_name or username)
        results = self.adapter.execute_query(query, params)
        return results[0] if results else None
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        query = "SELECT id, username, full_name, created_at FROM users WHERE id = %s"
        results = self.adapter.execute_query(query, (user_id,))
        return results[0] if results else None
    
    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user by username"""
        query = "SELECT id, username, full_name, created_at FROM users WHERE username = %s"
        results = self.adapter.execute_query(query, (username,))
        return results[0] if results else None
    
    def get_all_users(self) -> List[Dict[str, Any]]:
        """Get all users"""
        query = "SELECT id, username, full_name, created_at FROM users ORDER BY created_at DESC"
        return self.adapter.execute_query(query)
    
    def update_user(self, user_id: int, full_name: Optional[str] = None) -> bool:
        """Update user information"""
        if full_name:
            query = "UPDATE users SET full_name = %s WHERE id = %s"
            params = (full_name, user_id)
        else:
            return False
        
        affected = self.adapter.execute_update(query, params)
        return affected > 0
    
    def delete_user(self, user_id: int) -> bool:
        """Delete a user"""
        query = "DELETE FROM users WHERE id = %s"
        affected = self.adapter.execute_update(query, (user_id,))
        return affected > 0
    
    # Meal plan operations
    def create_meal_plan(self, user_id: int, start_date: date, end_date: date) -> Optional[Dict[str, Any]]:
        """Create a new meal plan"""
        query = """
            INSERT INTO meal_plans (user_id, start_date, end_date)
            VALUES (%s, %s, %s)
            RETURNING id, user_id, start_date, end_date, created_at
        """
        params = (user_id, start_date, end_date)
        results = self.adapter.execute_query(query, params)
        return results[0] if results else None
    
    def get_meal_plan_by_id(self, meal_plan_id: int) -> Optional[Dict[str, Any]]:
        """Get meal plan by ID"""
        query = "SELECT id, user_id, start_date, end_date, created_at FROM meal_plans WHERE id = %s"
        results = self.adapter.execute_query(query, (meal_plan_id,))
        return results[0] if results else None
    
    def get_meal_plans_by_user(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all meal plans for a user"""
        query = """
            SELECT id, user_id, start_date, end_date, created_at 
            FROM meal_plans 
            WHERE user_id = %s 
            ORDER BY created_at DESC
        """
        return self.adapter.execute_query(query, (user_id,))
    
    def delete_meal_plan(self, meal_plan_id: int) -> bool:
        """Delete a meal plan"""
        query = "DELETE FROM meal_plans WHERE id = %s"
        affected = self.adapter.execute_update(query, (meal_plan_id,))
        return affected > 0
    
    # Meal plan item operations
    def add_meal_plan_item(self, meal_plan_id: int, mealdb_id: int, meal_date: date, meal_type: str) -> Optional[Dict[str, Any]]:
        """Add a meal to a meal plan"""
        query = """
            INSERT INTO meal_plan_items (meal_plan_id, mealdb_id, meal_date, meal_type)
            VALUES (%s, %s, %s, %s)
            RETURNING id, meal_plan_id, mealdb_id, meal_date, meal_type
        """
        params = (meal_plan_id, mealdb_id, meal_date, meal_type)
        results = self.adapter.execute_query(query, params)
        return results[0] if results else None
    
    def get_meal_plan_items(self, meal_plan_id: int) -> List[Dict[str, Any]]:
        """Get all items in a meal plan"""
        query = """
            SELECT id, meal_plan_id, mealdb_id, meal_date, meal_type 
            FROM meal_plan_items 
            WHERE meal_plan_id = %s 
            ORDER BY meal_date, meal_type
        """
        return self.adapter.execute_query(query, (meal_plan_id,))
    
    def get_meal_plan_items_by_date(self, meal_plan_id: int, meal_date: date) -> List[Dict[str, Any]]:
        """Get meal plan items for a specific date"""
        query = """
            SELECT id, meal_plan_id, mealdb_id, meal_date, meal_type 
            FROM meal_plan_items 
            WHERE meal_plan_id = %s AND meal_date = %s 
            ORDER BY meal_type
        """
        return self.adapter.execute_query(query, (meal_plan_id, meal_date))
    
    def update_meal_plan_item(self, item_id: int, mealdb_id: Optional[int] = None, meal_type: Optional[str] = None) -> bool:
        """Update a meal plan item"""
        updates = []
        params = []
        param_count = 1
        
        if mealdb_id is not None:
            updates.append(f"mealdb_id = ${param_count}")
            params.append(mealdb_id)
            param_count += 1
        
        if meal_type is not None:
            updates.append(f"meal_type = ${param_count}")
            params.append(meal_type)
            param_count += 1
        
        if not updates:
            return False
        
        params.append(item_id)
        query = f"UPDATE meal_plan_items SET {', '.join(updates)} WHERE id = ${param_count}"
        affected = self.adapter.execute_update(query, tuple(params))
        return affected > 0
    
    def delete_meal_plan_item(self, item_id: int) -> bool:
        """Delete a meal plan item"""
        query = "DELETE FROM meal_plan_items WHERE id = %s"
        affected = self.adapter.execute_update(query, (item_id,))
        return affected > 0
    
    # Custom recipe operations (for recipe-interaction service)
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
        results = self.adapter.execute_query(query, params)
        return results[0] if results else None
    
    def get_custom_recipes_by_user(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all custom recipes for a user"""
        query = """
            SELECT id, user_id, name, category, area, instructions, image, tags, created_at 
            FROM custom_recipes 
            WHERE user_id = %s 
            ORDER BY created_at DESC
        """
        return self.adapter.execute_query(query, (user_id,))
    
    def get_custom_recipe_by_id(self, recipe_id: int) -> Optional[Dict[str, Any]]:
        """Get custom recipe by ID"""
        query = """
            SELECT id, user_id, name, category, area, instructions, image, tags, created_at 
            FROM custom_recipes 
            WHERE id = %s
        """
        results = self.adapter.execute_query(query, (recipe_id,))
        return results[0] if results else None
    
    def update_custom_recipe(self, recipe_id: int, recipe_data: Dict[str, Any]) -> bool:
        """Update a custom recipe"""
        updates = []
        params = []
        param_count = 1
        
        if "name" in recipe_data:
            updates.append(f"name = ${param_count}")
            params.append(recipe_data["name"])
            param_count += 1
        
        if "category" in recipe_data:
            updates.append(f"category = ${param_count}")
            params.append(recipe_data["category"])
            param_count += 1
        
        if "area" in recipe_data:
            updates.append(f"area = ${param_count}")
            params.append(recipe_data["area"])
            param_count += 1
        
        if "instructions" in recipe_data:
            updates.append(f"instructions = ${param_count}")
            params.append(recipe_data["instructions"])
            param_count += 1
        
        if "image" in recipe_data:
            updates.append(f"image = ${param_count}")
            params.append(recipe_data["image"])
            param_count += 1
        
        if "tags" in recipe_data:
            updates.append(f"tags = ${param_count}")
            params.append(recipe_data["tags"])
            param_count += 1
        
        if not updates:
            return False
        
        params.append(recipe_id)
        query = f"UPDATE custom_recipes SET {', '.join(updates)} WHERE id = ${param_count}"
        affected = self.adapter.execute_update(query, tuple(params))
        return affected > 0
    
    def delete_custom_recipe(self, recipe_id: int) -> bool:
        """Delete a custom recipe"""
        query = "DELETE FROM custom_recipes WHERE id = %s"
        affected = self.adapter.execute_update(query, (recipe_id,))
        return affected > 0
    
    # Database initialization
    def initialize_tables(self) -> bool:
        """Create all necessary tables"""
        schema_queries = [
            # Users table
            ("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    full_name VARCHAR(100),
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """, None),
            # Meal plans table
            ("""
                CREATE TABLE IF NOT EXISTS meal_plans (
                    id SERIAL PRIMARY KEY,
                    user_id INT REFERENCES users(id) ON DELETE CASCADE,
                    start_date DATE NOT NULL,
                    end_date DATE NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """, None),
            # Meal plan items table
            ("""
                CREATE TABLE IF NOT EXISTS meal_plan_items (
                    id SERIAL PRIMARY KEY,
                    meal_plan_id INT REFERENCES meal_plans(id) ON DELETE CASCADE,
                    mealdb_id INT NOT NULL,
                    meal_date DATE NOT NULL,
                    meal_type VARCHAR(20) NOT NULL
                )
            """, None),
            # Custom recipes table
            ("""
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
            """, None),
            # Custom recipe ingredients table
            ("""
                CREATE TABLE IF NOT EXISTS custom_recipe_ingredients (
                    id SERIAL PRIMARY KEY,
                    recipe_id INT REFERENCES custom_recipes(id) ON DELETE CASCADE,
                    ingredient_name VARCHAR(255) NOT NULL,
                    measure VARCHAR(100)
                )
            """, None)
        ]
        
        return self.adapter.execute_transaction(schema_queries)
    
    def close(self):
        """Close database connection"""
        self.adapter.disconnect()

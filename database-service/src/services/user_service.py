from typing import Optional, Dict, Any
from src.core.database import db_adapter
from src.schemas.user import UserCreate

class UserService:
    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        query = "SELECT * FROM users WHERE username = %s"
        with db_adapter.get_cursor() as cur:
            cur.execute(query, (username,))
            return cur.fetchone()

    def get_users(self, skip: int = 0, limit: int = 100) -> list:
        query = "SELECT * FROM users ORDER BY id OFFSET %s LIMIT %s"
        with db_adapter.get_cursor() as cur:
            cur.execute(query, (skip, limit))
            return cur.fetchall()

    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        query = "SELECT * FROM users WHERE id = %s"
        with db_adapter.get_cursor() as cur:
            cur.execute(query, (user_id,))
            return cur.fetchone()

    def create_user(self, user: UserCreate) -> Optional[int]:
        query = """
            INSERT INTO users (username, hashed_password, email, full_name)
            VALUES (%s, %s, %s, %s)
            RETURNING id
        """
        try:
            with db_adapter.get_cursor() as cur:
                cur.execute(query, (
                    user.username, 
                    user.hashed_password, 
                    user.email, 
                    user.full_name
                ))
                result = cur.fetchone()
                return result['id'] if result else None
        except Exception as e:
            print(f"Error creating user: {e}")
            return None
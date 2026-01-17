from typing import List, Dict, Any, Optional
from src.core.database import db_adapter
from datetime import datetime

class ReviewService:
    
    def create_review(self, user_id: int, recipe_id: int, rating: int, comment: str) -> Optional[int]:
        query = """
            INSERT INTO reviews (user_id, recipe_id, rating, comment, created_at)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
        """
        try:
            with db_adapter.get_cursor() as cur:
                cur.execute(query, (user_id, recipe_id, rating, comment, datetime.now()))
                result = cur.fetchone()
                return result['id'] if result else None
        except Exception as e:
            print(f"Error creating review: {e}")
            return None

    def get_reviews_by_recipe(self, recipe_id: int) -> List[Dict[str, Any]]:
        query = """
            SELECT r.*, u.username 
            FROM reviews r
            LEFT JOIN users u ON r.user_id = u.id
            WHERE r.recipe_id = %s
            ORDER BY r.created_at DESC
        """
        with db_adapter.get_cursor() as cur:
            cur.execute(query, (recipe_id,))
            return cur.fetchall()

    def delete_review(self, review_id: int) -> bool:
        query = "DELETE FROM reviews WHERE id = %s"
        try:
            with db_adapter.get_cursor() as cur:
                cur.execute(query, (review_id,))
                return cur.rowcount > 0
        except Exception as e:
            print(f"Error deleting review: {e}")
            return False
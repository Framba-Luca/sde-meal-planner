from typing import List, Dict, Any, Optional
from src.core.database import db_adapter
from src.schemas.meal import MealPlanCreate, MealPlanItemCreate

class MealService:
    def create_meal_plan(self, plan: MealPlanCreate) -> Optional[int]:
        query = """
            INSERT INTO meal_plans (user_id, start_date, end_date)
            VALUES (%s, %s, %s)
            RETURNING id
        """
        try:
            with db_adapter.get_cursor() as cur:
                cur.execute(query, (plan.user_id, plan.start_date, plan.end_date))
                result = cur.fetchone()
                return result['id'] if result else None
        except Exception as e:
            print(f"Error creating meal plan: {e}")
            return None

    def get_meal_plans_by_user(self, user_id: int) -> List[Dict[str, Any]]:
        query = "SELECT * FROM meal_plans WHERE user_id = %s ORDER BY start_date DESC"
        with db_adapter.get_cursor() as cur:
            cur.execute(query, (user_id,))
            return cur.fetchall()

    def add_meal_item(self, item: MealPlanItemCreate) -> Optional[int]:
        query = """
            INSERT INTO meal_plan_items (meal_plan_id, mealdb_id, meal_date, meal_type)
            VALUES (%s, %s, %s, %s)
            RETURNING id
        """
        try:
            with db_adapter.get_cursor() as cur:
                cur.execute(query, (item.meal_plan_id, item.mealdb_id, item.meal_date, item.meal_type))
                result = cur.fetchone()
                return result['id'] if result else None
        except Exception:
            return None
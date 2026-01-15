from typing import List, Dict, Any, Optional
from src.core.database import db_adapter
from src.schemas.meal import MealPlanCreate, MealPlanItemCreate, MealPlanItemUpdate

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

    def get_meal_plan(self, meal_plan_id: int) -> Optional[Dict[str, Any]]:
        query = "SELECT * FROM meal_plans WHERE id = %s"
        with db_adapter.get_cursor() as cur:
            cur.execute(query, (meal_plan_id,))
            result = cur.fetchone()
            return result

    def get_meal_plans_by_user(self, user_id: int) -> List[Dict[str, Any]]:
        query = "SELECT * FROM meal_plans WHERE user_id = %s ORDER BY start_date DESC"
        with db_adapter.get_cursor() as cur:
            cur.execute(query, (user_id,))
            return cur.fetchall()

    def delete_meal_plan(self, meal_plan_id: int) -> bool:
        query = "DELETE FROM meal_plans WHERE id = %s"
        try:
            with db_adapter.get_cursor() as cur:
                cur.execute(query, (meal_plan_id,))
                return cur.rowcount > 0
        except Exception as e:
            print(f"Error deleting meal plan: {e}")
            return False

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
        except Exception as e:
            print(f"Error adding meal item: {e}")
            return None

    def get_meal_plan_items(self, meal_plan_id: int) -> List[Dict[str, Any]]:
        query = "SELECT * FROM meal_plan_items WHERE meal_plan_id = %s ORDER BY meal_date, meal_type"
        with db_adapter.get_cursor() as cur:
            cur.execute(query, (meal_plan_id,))
            return cur.fetchall()

    def update_meal_item(self, item_id: int, item_update: MealPlanItemUpdate) -> Optional[Dict[str, Any]]:
        # Build dynamic update query based on provided fields
        update_fields = []
        values = []
        
        if item_update.mealdb_id is not None:
            update_fields.append("mealdb_id = %s")
            values.append(item_update.mealdb_id)
        
        if item_update.meal_type is not None:
            update_fields.append("meal_type = %s")
            values.append(item_update.meal_type)
        
        if not update_fields:
            return None
        
        values.append(item_id)
        query = f"""
            UPDATE meal_plan_items 
            SET {', '.join(update_fields)}
            WHERE id = %s
            RETURNING *
        """
        
        try:
            with db_adapter.get_cursor() as cur:
                cur.execute(query, values)
                result = cur.fetchone()
                return result
        except Exception as e:
            print(f"Error updating meal item: {e}")
            return None

    def delete_meal_item(self, item_id: int) -> bool:
        query = "DELETE FROM meal_plan_items WHERE id = %s"
        try:
            with db_adapter.get_cursor() as cur:
                cur.execute(query, (item_id,))
                return cur.rowcount > 0
        except Exception as e:
            print(f"Error deleting meal item: {e}")
            return False
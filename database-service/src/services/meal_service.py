from typing import List, Optional, Dict, Any
from sqlmodel import Session, select
from datetime import date

# Import DB models
from src.models.meal_model import MealPlan, MealPlanItem
# Import Pydantic schemas (input/output)
from src.schemas.meal import MealPlanCreate, MealPlanItemCreate, MealPlanItemUpdate


class MealService:
    def __init__(self, session: Session):
        self.session = session

    # --- MEAL PLANS (Header) ---

    def create_meal_plan(self, plan: MealPlanCreate) -> int:
        """Creates a new empty weekly meal plan."""
        db_plan = MealPlan(
            user_id=plan.user_id,
            start_date=plan.start_date,
            end_date=plan.end_date
        )
        self.session.add(db_plan)
        self.session.commit()
        self.session.refresh(db_plan)
        return db_plan.id

    def get_meal_plan(self, meal_plan_id: int) -> Optional[MealPlan]:
        return self.session.get(MealPlan, meal_plan_id)

    def get_meal_plans_by_user(self, user_id: int) -> List[MealPlan]:
        statement = (
            select(MealPlan)
            .where(MealPlan.user_id == user_id)
            .order_by(MealPlan.start_date.desc())
        )
        return self.session.exec(statement).all()

    def delete_meal_plan(self, meal_plan_id: int) -> bool:
        plan = self.session.get(MealPlan, meal_plan_id)
        if not plan:
            return False
        # Cascade delete on items is handled automatically
        self.session.delete(plan)
        self.session.commit()
        return True

    # --- MEAL ITEMS (Plan rows) ---

    def add_meal_item(self, item: MealPlanItemCreate) -> int:
        """Adds a recipe to a specific day of the meal plan."""
        db_item = MealPlanItem(
            meal_plan_id=item.meal_plan_id,
            mealdb_id=item.mealdb_id,
            meal_date=item.meal_date,
            meal_type=item.meal_type
        )
        self.session.add(db_item)
        self.session.commit()
        self.session.refresh(db_item)
        return db_item.id

    def get_meal_plan_items(self, meal_plan_id: int) -> List[MealPlanItem]:
        statement = select(MealPlanItem).where(
            MealPlanItem.meal_plan_id == meal_plan_id
        )
        return self.session.exec(statement).all()

    def update_meal_item(
        self,
        item_id: int,
        item_update: MealPlanItemUpdate
    ) -> Optional[MealPlanItem]:
        db_item = self.session.get(MealPlanItem, item_id)
        if not db_item:
            return None

        # Update only provided fields (PATCH behavior)
        item_data = item_update.dict(exclude_unset=True)
        for key, value in item_data.items():
            setattr(db_item, key, value)

        self.session.add(db_item)
        self.session.commit()
        self.session.refresh(db_item)
        return db_item

    def delete_meal_item(self, item_id: int) -> bool:
        item = self.session.get(MealPlanItem, item_id)
        if not item:
            return False
        self.session.delete(item)
        self.session.commit()
        return True

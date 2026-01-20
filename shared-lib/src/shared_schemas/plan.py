from pydantic import BaseModel, ConfigDict
from datetime import date, datetime
from typing import List

# --- ITEM BASE ---
class MealPlanItemBase(BaseModel):
    mealdb_id: int
    meal_date: date
    meal_type: str

class MealPlanItemCreate(MealPlanItemBase):
    meal_plan_id: int

class MealPlanItemResponse(MealPlanItemBase):
    id: int
    meal_plan_id: int
    model_config = ConfigDict(from_attributes=True)

# --- PLAN BASE ---
class MealPlanBase(BaseModel):
    start_date: date
    end_date: date

class MealPlanCreate(MealPlanBase):
    user_id: int

class MealPlanResponse(MealPlanBase):
    id: int
    user_id: int
    created_at: datetime
    items: List[MealPlanItemResponse] = []

    model_config = ConfigDict(from_attributes=True)
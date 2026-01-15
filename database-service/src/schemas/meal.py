from pydantic import BaseModel
from datetime import date, datetime
from typing import List, Optional

# --- Meal Plans ---
class MealPlanCreate(BaseModel):
    user_id: int
    start_date: date
    end_date: date

class MealPlanResponse(BaseModel):
    id: int
    user_id: int
    start_date: date
    end_date: date
    created_at: datetime

# --- Meal Items ---
class MealPlanItemCreate(BaseModel):
    meal_plan_id: int
    mealdb_id: int
    meal_date: date
    meal_type: str

class MealPlanItemUpdate(BaseModel):
    mealdb_id: Optional[int] = None
    meal_type: Optional[str] = None

class MealPlanItemResponse(MealPlanItemCreate):
    id: int
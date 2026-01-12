from pydantic import BaseModel
from datetime import date
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
    created_at: str | date

# --- Meal Items ---
class MealPlanItemCreate(BaseModel):
    meal_plan_id: int
    mealdb_id: int
    meal_date: date
    meal_type: str

class MealPlanItemResponse(MealPlanItemCreate):
    id: int
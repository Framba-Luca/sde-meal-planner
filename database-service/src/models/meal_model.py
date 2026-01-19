from typing import Optional, List
from datetime import date, datetime
from sqlmodel import SQLModel, Field, Relationship


# Single meal plan entry (Breakfast, Lunch, Dinner)
class MealPlanItem(SQLModel, table=True):
    __tablename__ = "meal_plan_items"

    id: Optional[int] = Field(default=None, primary_key=True)
    meal_plan_id: int = Field(foreign_key="meal_plans.id")

    mealdb_id: Optional[int] = None  # Quick external reference
    meal_date: date
    meal_type: str  # 'breakfast', 'lunch', 'dinner'

    # Inverse relationship
    meal_plan: "MealPlan" = Relationship(back_populates="items")


# Weekly meal plan
class MealPlan(SQLModel, table=True):
    __tablename__ = "meal_plans"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")

    start_date: date
    end_date: date
    created_at: datetime = Field(default_factory=datetime.now)

    # Relationship: one plan has many items.
    # Cascade delete removes items when the plan is deleted.
    items: List[MealPlanItem] = Relationship(
        back_populates="meal_plan",
        sa_relationship_kwargs={"cascade": "all, delete"}
    )

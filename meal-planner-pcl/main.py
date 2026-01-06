"""
Meal Planner Service - REST API endpoints
"""
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from typing import Optional, List
from datetime import date
from services import MealPlannerService

app = FastAPI(title="Meal Planner Service", version="1.0.0")

# Initialize service
meal_planner = MealPlannerService()


# Pydantic models
class MealProposalRequest(BaseModel):
    ingredient: Optional[str] = None


class MealPlanCreateRequest(BaseModel):
    user_id: int
    start_date: Optional[date] = None
    end_date: date


class MealPlanGenerateRequest(BaseModel):
    user_id: int
    num_days: int
    start_date: Optional[date] = None
    ingredient: Optional[str] = None


class MealPlanItemUpdateRequest(BaseModel):
    mealdb_id: Optional[int] = None
    meal_type: Optional[str] = None


# Endpoints
@app.get("/")
async def root():
    """Root endpoint"""
    return {"service": "Meal Planner Service", "status": "running"}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.post("/propose")
async def propose_meal(request: MealProposalRequest):
    """Propose a single meal"""
    meal = meal_planner.propose_meal(request.ingredient)
    if meal:
        return meal
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="No meal found"
    )


@app.post("/meal-plans", response_model=dict)
async def create_meal_plan(request: MealPlanCreateRequest):
    """Create a new meal plan"""
    if request.start_date is None:
        start_date = date.today()
    else:
        start_date = request.start_date
    
    meal_plan = meal_planner.create_meal_plan(request.user_id, start_date, request.end_date)
    if meal_plan:
        return meal_plan
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Failed to create meal plan"
    )


@app.post("/meal-plans/generate", response_model=dict)
async def generate_meal_plan(request: MealPlanGenerateRequest):
    """Generate a complete meal plan for specified number of days"""
    meal_plan = meal_planner.generate_meal_plan(
        user_id=request.user_id,
        num_days=request.num_days,
        start_date=request.start_date,
        ingredient=request.ingredient
    )
    if meal_plan:
        return meal_plan
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Failed to generate meal plan"
    )


@app.get("/meal-plans/{meal_plan_id}")
async def get_meal_plan(meal_plan_id: int):
    """Get a meal plan by ID"""
    meal_plan = meal_planner.get_meal_plan(meal_plan_id)
    if meal_plan:
        return meal_plan
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Meal plan not found"
    )


@app.get("/meal-plans/{meal_plan_id}/items")
async def get_meal_plan_items(meal_plan_id: int):
    """Get all items in a meal plan"""
    items = meal_planner.get_meal_plan_items(meal_plan_id)
    if items is not None:
        return {"meal_plan_id": meal_plan_id, "items": items}
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Meal plan items not found"
    )


@app.get("/meal-plans/user/{user_id}")
async def get_user_meal_plans(user_id: int):
    """Get all meal plans for a user"""
    meal_plans = meal_planner.get_user_meal_plans(user_id)
    if meal_plans is not None:
        return {"user_id": user_id, "meal_plans": meal_plans}
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="No meal plans found for user"
    )


@app.delete("/meal-plans/{meal_plan_id}")
async def delete_meal_plan(meal_plan_id: int):
    """Delete a meal plan"""
    success = meal_planner.delete_meal_plan(meal_plan_id)
    if success:
        return {"status": "success", "message": "Meal plan deleted"}
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Failed to delete meal plan"
    )


@app.put("/meal-plan-items/{item_id}")
async def update_meal_in_plan(item_id: int, request: MealPlanItemUpdateRequest):
    """Update a meal in a meal plan"""
    success = meal_planner.update_meal_in_plan(
        item_id=item_id,
        mealdb_id=request.mealdb_id,
        meal_type=request.meal_type
    )
    if success:
        return {"status": "success", "message": "Meal updated"}
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Failed to update meal"
    )


@app.delete("/meal-plan-items/{item_id}")
async def delete_meal_from_plan(item_id: int):
    """Delete a meal from a meal plan"""
    success = meal_planner.delete_meal_from_plan(item_id)
    if success:
        return {"status": "success", "message": "Meal deleted"}
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Failed to delete meal"
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)

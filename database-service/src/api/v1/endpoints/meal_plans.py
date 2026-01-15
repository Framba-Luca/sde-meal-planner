from typing import List, Dict, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from src.schemas.meal import MealPlanCreate, MealPlanResponse, MealPlanItemCreate, MealPlanItemResponse
from src.services.meal_service import MealService
from src.api.deps import verify_token, verify_internal_service_token

router = APIRouter()
meal_service = MealService()

# Schema for updating meal plan items
class MealPlanItemUpdate(BaseModel):
    mealdb_id: Optional[int] = None
    meal_type: Optional[str] = None

@router.post("/", response_model=MealPlanResponse, status_code=status.HTTP_201_CREATED)
async def create_meal_plan(
    plan: MealPlanCreate,
    token_payload: Dict = Depends(verify_internal_service_token) # <--- Internal Service Auth
):
    """Create a new meal plan."""
    plan_id = meal_service.create_meal_plan(plan)
    if not plan_id:
        raise HTTPException(status_code=400, detail="Failed to create meal plan")
    
    # In a real app, you might fetch the full object again. 
    # Here we construct a minimal response.
    return {
        "id": plan_id, 
        "user_id": plan.user_id, 
        "start_date": plan.start_date, 
        "end_date": plan.end_date,
        "created_at": datetime.utcnow()
    }

@router.get("/{meal_plan_id}", response_model=MealPlanResponse)
async def get_meal_plan(
    meal_plan_id: int,
    token_payload: Dict = Depends(verify_internal_service_token)
):
    """Get a meal plan by ID."""
    result = meal_service.get_meal_plan(meal_plan_id)
    if not result:
        raise HTTPException(status_code=404, detail="Meal plan not found")
    return result

@router.get("/user/{user_id}", response_model=List[MealPlanResponse])
async def get_meal_plans_by_user(
    user_id: int,
    token_payload: Dict = Depends(verify_internal_service_token)
):
    """Get all meal plans for a specific user."""
    results = meal_service.get_meal_plans_by_user(user_id)
    return results

@router.delete("/{meal_plan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_meal_plan(
    meal_plan_id: int,
    token_payload: Dict = Depends(verify_internal_service_token)
):
    """Delete a meal plan."""
    success = meal_service.delete_meal_plan(meal_plan_id)
    if not success:
        raise HTTPException(status_code=404, detail="Meal plan not found")
    return None

@router.post("/items/", response_model=MealPlanItemResponse, status_code=status.HTTP_201_CREATED)
async def add_meal_item(
    item: MealPlanItemCreate,
    token_payload: Dict = Depends(verify_internal_service_token)
):
    """Add a meal item (recipe) to a plan."""
    item_id = meal_service.add_meal_item(item)
    if not item_id:
        raise HTTPException(status_code=400, detail="Failed to add item")
    
    return {**item.dict(), "id": item_id}

@router.get("/items/{meal_plan_id}", response_model=List[MealPlanItemResponse])
async def get_meal_plan_items(
    meal_plan_id: int,
    token_payload: Dict = Depends(verify_internal_service_token)
):
    """Get all items for a specific meal plan."""
    results = meal_service.get_meal_plan_items(meal_plan_id)
    return results

@router.put("/items/{item_id}", response_model=MealPlanItemResponse)
async def update_meal_item(
    item_id: int,
    item_update: MealPlanItemUpdate,
    token_payload: Dict = Depends(verify_internal_service_token)
):
    """Update a meal item in a plan."""
    result = meal_service.update_meal_item(item_id, item_update)
    if not result:
        raise HTTPException(status_code=404, detail="Meal item not found")
    return result

@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_meal_item(
    item_id: int,
    token_payload: Dict = Depends(verify_internal_service_token)
):
    """Delete a meal item from a plan."""
    success = meal_service.delete_meal_item(item_id)
    if not success:
        raise HTTPException(status_code=404, detail="Meal item not found")
    return None
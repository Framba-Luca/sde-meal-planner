from typing import List, Dict
from fastapi import APIRouter, HTTPException, status, Depends
from src.schemas.meal import MealPlanCreate, MealPlanResponse, MealPlanItemCreate, MealPlanItemResponse
from src.services.meal_service import MealService
from src.api.deps import verify_token, verify_internal_service_token

router = APIRouter()
meal_service = MealService()

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
        "created_at": "now" # Placeholder, or fetch from DB
    }

@router.get("/user/{user_id}", response_model=List[MealPlanResponse])
async def get_meal_plans_by_user(
    user_id: int,
    token_payload: Dict = Depends(verify_internal_service_token)
):
    """Get all meal plans for a specific user."""
    results = meal_service.get_meal_plans_by_user(user_id)
    return results

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
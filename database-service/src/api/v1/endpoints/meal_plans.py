from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlmodel import Session

from src.core.database import get_session
from src.services.meal_service import MealService
from src.schemas.meal import (
    MealPlanCreate, MealPlanResponse,
    MealPlanItemCreate, MealPlanItemResponse
)

router = APIRouter()

# --- DEPENDENCY INJECTION ---
# Provides a MealService instance for each request
def get_meal_service(session: Session = Depends(get_session)) -> MealService:
    return MealService(session)


# --- MEAL PLAN ROUTES ---

@router.post("/", response_model=MealPlanResponse, status_code=status.HTTP_201_CREATED)
async def create_meal_plan(
    plan: MealPlanCreate,
    service: MealService = Depends(get_meal_service)
):
    """
    Creates a new weekly meal plan.
    Returns the full plan after creation.
    """
    plan_id = service.create_meal_plan(plan)
    return service.get_meal_plan(plan_id)


@router.get("/user/{user_id}", response_model=List[MealPlanResponse])
async def get_plans_by_user(
    user_id: int,
    service: MealService = Depends(get_meal_service)
):
    """
    Retrieves all meal plans for a specific user.
    """
    return service.get_meal_plans_by_user(user_id)


@router.get("/{plan_id}", response_model=MealPlanResponse)
async def get_plan_by_id(
    plan_id: int,
    service: MealService = Depends(get_meal_service)
):
    """
    Retrieves a meal plan by its ID.
    """
    plan = service.get_meal_plan(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Meal Plan not found")
    return plan


@router.delete("/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_meal_plan(
    plan_id: int,
    service: MealService = Depends(get_meal_service)
):
    """
    Deletes a meal plan by its ID.
    Cascade deletes all items associated with the plan.
    """
    if not service.delete_meal_plan(plan_id):
        raise HTTPException(status_code=404, detail="Meal Plan not found")
    return


# --- MEAL PLAN ITEM ROUTES ---

@router.post("/items", response_model=MealPlanItemResponse, status_code=status.HTTP_201_CREATED)
async def add_meal_item(
    item: MealPlanItemCreate,
    service: MealService = Depends(get_meal_service)
):
    """
    Adds a recipe item to a specific day of a meal plan.
    Returns the created item with its ID.
    """
    item_id = service.add_meal_item(item)
    # Simple reconstruction for the response
    return MealPlanItemResponse(id=item_id, **item.dict())


@router.get("/{plan_id}/items", response_model=List[MealPlanItemResponse])
async def get_plan_items(
    plan_id: int,
    service: MealService = Depends(get_meal_service)
):
    """
    Retrieves all items for a specific meal plan.
    """
    return service.get_meal_plan_items(plan_id)


@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_meal_item(
    item_id: int,
    service: MealService = Depends(get_meal_service)
):
    """
    Deletes a single meal item by its ID.
    """
    if not service.delete_meal_item(item_id):
        raise HTTPException(status_code=404, detail="Item not found")
    return

from typing import List, Dict
from fastapi import APIRouter, HTTPException, status, Depends
from src.schemas.recipe import CustomRecipeCreate, CustomRecipeResponse
from src.services.recipe_service import RecipeService
from src.api.deps import verify_internal_service_token

router = APIRouter()
recipe_service = RecipeService()

@router.post("/", response_model=CustomRecipeResponse, status_code=status.HTTP_201_CREATED)
async def create_custom_recipe(
    recipe: CustomRecipeCreate,
    token_payload: Dict = Depends(verify_internal_service_token)
):
    """Create a new custom recipe."""
    recipe_id = recipe_service.create_custom_recipe(recipe)
    if not recipe_id:
        raise HTTPException(status_code=400, detail="Failed to create recipe")
    
    created_recipe = recipe_service.get_custom_recipe_by_id(recipe_id)
    return created_recipe

@router.get("/{recipe_id}", response_model=CustomRecipeResponse)
async def get_custom_recipe(
    recipe_id: int,
    token_payload: Dict = Depends(verify_internal_service_token)
):
    """Get a recipe by ID."""
    result = recipe_service.get_custom_recipe_by_id(recipe_id)
    if not result:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return result

@router.get("/user/{user_id}", response_model=List[CustomRecipeResponse])
async def get_custom_recipes_by_user(
    user_id: int,
    token_payload: Dict = Depends(verify_internal_service_token)
):
    """Get all custom recipes created by a user."""
    results = recipe_service.get_custom_recipes_by_user(user_id)
    return results

@router.put("/{recipe_id}", response_model=CustomRecipeResponse)
async def update_custom_recipe(
    recipe_id: int,
    recipe_data: Dict,
    token_payload: Dict = Depends(verify_internal_service_token)
):
    """Update a custom recipe."""
    success = recipe_service.update_custom_recipe(recipe_id, recipe_data)
    if not success:
        raise HTTPException(status_code=404, detail="Recipe not found or update failed")
    
    updated_recipe = recipe_service.get_custom_recipe_by_id(recipe_id)
    return updated_recipe

@router.delete("/{recipe_id}")
async def delete_custom_recipe(
    recipe_id: int,
    token_payload: Dict = Depends(verify_internal_service_token)
):
    """Delete a custom recipe."""
    success = recipe_service.delete_custom_recipe(recipe_id)
    if success:
        return {"status": "success", "message": "Recipe deleted"}
    raise HTTPException(status_code=404, detail="Recipe not found")
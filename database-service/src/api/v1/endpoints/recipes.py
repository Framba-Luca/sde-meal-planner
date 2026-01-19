from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlmodel import Session

from src.core.database import get_session
from src.services.recipe_service import RecipeService
from src.schemas.recipe import CustomRecipeCreate, CustomRecipeResponse, ShadowRecipeCreate

router = APIRouter()

# --- DEPENDENCY INJECTION ---
# Provides a RecipeService instance for each request
def get_recipe_service(session: Session = Depends(get_session)) -> RecipeService:
    return RecipeService(session)


# --- ROUTES ---

@router.post("/custom", response_model=CustomRecipeResponse, status_code=status.HTTP_201_CREATED)
async def create_custom_recipe(
    recipe: CustomRecipeCreate,
    service: RecipeService = Depends(get_recipe_service)  # Service injection
):
    """
    Creates a new custom recipe.
    Returns the full recipe after creation.
    """
    recipe_id = service.create_custom_recipe(recipe)
    return service.get_custom_recipe_by_id(recipe_id)


@router.get("/user/{user_id}", response_model=List[CustomRecipeResponse])
async def get_user_recipes(
    user_id: int,
    service: RecipeService = Depends(get_recipe_service)
):
    """
    Retrieves all custom recipes for a specific user.
    """
    return service.get_recipes_by_user(user_id)


@router.get("/{recipe_id}", response_model=CustomRecipeResponse)
async def get_recipe_details(
    recipe_id: int,
    service: RecipeService = Depends(get_recipe_service)
):
    """
    Retrieves the details of a custom recipe by its ID.
    """
    recipe = service.get_custom_recipe_by_id(recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return recipe


@router.delete("/{recipe_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_recipe(
    recipe_id: int,
    service: RecipeService = Depends(get_recipe_service)
):
    """
    Deletes a custom recipe by its ID.
    Cascade deletes ingredients as well.
    """
    if not service.delete_custom_recipe(recipe_id):
        raise HTTPException(status_code=404, detail="Recipe not found")
    return


@router.post("/shadow", status_code=status.HTTP_200_OK)
async def create_shadow_recipe(
    recipe: ShadowRecipeCreate,
    service: RecipeService = Depends(get_recipe_service)
):
    """
    Creates or updates a shadow recipe (external API cache).
    Returns the ID of the synced recipe and status.
    """
    recipe_id = service.create_shadow_recipe(recipe.dict())
    return {"id": recipe_id, "status": "synced"}

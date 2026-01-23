from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from sqlmodel import Session

# Database session dependency
from src.core.database import get_session

# Services
from src.services.recipe_service import RecipeService

# Schemas
# Make sure CustomRecipeResponse includes the "ingredients" field
from src.schemas.recipe import (
    CustomRecipeCreate,
    CustomRecipeResponse,
    ShadowRecipeCreate,
    RecipeUpdate
)

router = APIRouter()

# --- DEPENDENCY INJECTION ---
# Provides a RecipeService instance for each request
def get_recipe_service(session: Session = Depends(get_session)) -> RecipeService:
    return RecipeService(session)


# --- RECIPE ROUTES ---

@router.post("/", response_model=CustomRecipeResponse, status_code=status.HTTP_201_CREATED)
async def create_recipe(
    recipe: CustomRecipeCreate,
    service: RecipeService = Depends(get_recipe_service)
):
    """
    Creates a new custom recipe owned by a user.
    Returns the created recipe with all its details.
    """
    # Pass the Pydantic object directly to the service
    created_recipe = service.create_custom_recipe(recipe)
    return created_recipe


@router.get("/user/{user_id}", response_model=List[CustomRecipeResponse])
async def get_user_recipes(
    user_id: int,
    service: RecipeService = Depends(get_recipe_service)
):
    """
    Retrieves all custom recipes created by a specific user.
    """
    return service.get_recipes_by_user(user_id)


@router.get("/{recipe_id}", response_model=CustomRecipeResponse)
async def get_recipe_detail(
    recipe_id: int,
    service: RecipeService = Depends(get_recipe_service)
):
    """
    Retrieves a custom recipe by its ID.
    """
    recipe = service.get_custom_recipe_by_id(recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return recipe

@router.get("", response_model=List[CustomRecipeResponse])
async def get_recipe_detail(
    query: Optional[str] = None,
    category: Optional[str] = None,
    area: Optional[str] = None,
    ingredient: Optional[str] = None,
    service: RecipeService = Depends(get_recipe_service)
):
    """
    Retrieves a custom by the query
    """
    recipe = service.get_recipe(query, category, area, ingredient)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return recipe

@router.post("/shadow", status_code=status.HTTP_200_OK)
async def create_shadow_recipe(
    recipe: ShadowRecipeCreate,
    service: RecipeService = Depends(get_recipe_service)
):
    """
    Creates or updates a shadow recipe based on an external source.
    Used to synchronize external recipes into the local database.
    """
    recipe_id = service.create_shadow_recipe(recipe.dict())
    return {"id": recipe_id, "status": "synced"}

@router.put("/{recipe_id}", response_model=CustomRecipeResponse)
async def update_recipe(
    recipe_id: int,
    recipe_update: RecipeUpdate,
    service: RecipeService = Depends(get_recipe_service)
):
    """
    Updates an existing custom recipe.
    """
    updated_recipe = service.update_custom_recipe(recipe_id, recipe_update)
    
    if not updated_recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
        
    return updated_recipe

@router.delete("/{recipe_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_recipe(
    recipe_id: int,
    service: RecipeService = Depends(get_recipe_service)
):
    """
    Deletes a custom recipe by ID.
    """
    success = service.delete_custom_recipe(recipe_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Recipe not found")
    
    return
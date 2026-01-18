from fastapi import APIRouter, Depends, HTTPException
from typing import List
from src.schemas.recipe import RecipeCreate, RecipeUpdate, RecipeResponse
from src.services.recipe_service import RecipeService
from src.api.deps import get_recipe_service

router = APIRouter()

@router.post("/", response_model=RecipeResponse)
async def create(recipe: RecipeCreate, service: RecipeService = Depends(get_recipe_service)):
    res = service.create_recipe(recipe.user_id, recipe.dict())
    if not res: raise HTTPException(400, "Error creating recipe")
    return res

@router.get("/user/{user_id}", response_model=List[RecipeResponse])
async def get_user_recipes(user_id: int, service: RecipeService = Depends(get_recipe_service)):
    return service.get_user_recipes(user_id)


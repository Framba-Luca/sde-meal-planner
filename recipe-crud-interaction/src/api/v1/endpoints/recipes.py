from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from src.schemas.recipe import RecipeCreate, RecipeUpdate, RecipeResponse, RecipeUnifiedDetail, RecipeUnifiedSummary
from src.services.recipe_service import RecipeService
from src.api.deps import get_recipe_service, get_current_user

router = APIRouter()

@router.post("/", response_model=RecipeResponse)
async def create(recipe: RecipeCreate, 
                 service: RecipeService = Depends(get_recipe_service), 
                 current_user_id: int = Depends(get_current_user)):
    
    recipe.user_id = current_user_id
    res = service.create_recipe(current_user_id, recipe.dict())
    if not res: raise HTTPException(400, "Error creating recipe")
    return res

@router.put("/{recipe_id}", response_model=RecipeResponse)
async def update_recipe(
    recipe_id: int,
    recipe_update: RecipeUpdate,
    service: RecipeService = Depends(get_recipe_service),
    current_user_id: int = Depends(get_current_user)
):
    data = recipe_update.dict(exclude_unset=True)
    result = service.update_recipe(current_user_id, recipe_id, data)
    
    if result and "error" in result:
        code = result.get("code", 400)
        raise HTTPException(status_code=code, detail=result["error"])
        
    return result

@router.delete("/{recipe_id}")
async def delete_recipe(
    recipe_id: int,
    service: RecipeService = Depends(get_recipe_service),
    current_user_id: int = Depends(get_current_user)
):
    result = service.delete_recipe(current_user_id, recipe_id)
    
    if result and "error" in result:
        code = result.get("code", 400)
        raise HTTPException(status_code=code, detail=result["error"])
        
    return {"status": "success", "message": "Recipe deleted"}

@router.get("/user/{user_id}", response_model=List[RecipeResponse])
async def get_user_recipes(user_id: int, service: RecipeService = Depends(get_recipe_service)):
    return service.get_user_recipes(user_id)

@router.get("/search", response_model=List[RecipeUnifiedSummary])
async def search_recipes(
    q: Optional[str] = Query(None, description="Search by name"),
    category: Optional[str] = Query(None, description="Filter by category"),
    area: Optional[str] = Query(None, description="Filter by area"),
    ingredient: Optional[str] = Query(None, description="Filter by ingredient"),
    service: RecipeService = Depends(get_recipe_service)
):
    if not any([q, category, area, ingredient]):
        return []

    return service.search_unified(
        query=q,
        category=category,
        area=area,
        ingredient=ingredient
    )

@router.get("/{recipe_id}", response_model=RecipeUnifiedDetail)
async def recipe_by_id(
    recipe_id: int,
    source: Optional[str] = Query(None, description="Set to 'external' to force external fetch"),
    service: RecipeService = Depends(get_recipe_service),
):
    """
    Get details of a single recipe. 
    If 'source=external' is passed, it skips internal DB lookup.
    """
    result = service.get_recipe(recipe_id, source=source)
    
    if not result:
        raise HTTPException(status_code=404, detail="Recipe not found")
        
    return result
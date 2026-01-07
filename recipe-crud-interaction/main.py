"""
Recipe CRUD Interaction Service - REST API endpoints
"""
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from typing import Optional, List
from services import RecipeCRUDService

app = FastAPI(title="Recipe CRUD Interaction Service", version="1.0.0")

# Initialize service
recipe_crud = RecipeCRUDService()


# Pydantic models
class RecipeCreate(BaseModel):
    user_id: int
    name: str
    category: Optional[str] = ""
    area: Optional[str] = ""
    instructions: Optional[str] = ""
    image: Optional[str] = ""
    tags: Optional[str] = ""


class RecipeUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    area: Optional[str] = None
    instructions: Optional[str] = None
    image: Optional[str] = None
    tags: Optional[str] = None


class RecipeResponse(BaseModel):
    id: int
    user_id: int
    name: str
    category: str
    area: str
    instructions: str
    image: str
    tags: str
    created_at: str


# Endpoints
@app.get("/")
async def root():
    """Root endpoint"""
    return {"service": "Recipe CRUD Interaction Service", "status": "running"}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.post("/recipes", response_model=RecipeResponse)
async def create_recipe(recipe: RecipeCreate):
    """Create a new custom recipe"""
    # Validate recipe data
    is_valid, error_message = recipe_crud.validate_recipe_data(recipe.dict())
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_message
        )
    
    result = recipe_crud.create_custom_recipe(recipe.user_id, recipe.dict())
    if result:
        return RecipeResponse(**result)
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Failed to create recipe"
    )


@app.get("/recipes/{recipe_id}", response_model=RecipeResponse)
async def get_recipe(recipe_id: int):
    """Get a custom recipe by ID"""
    result = recipe_crud.get_custom_recipe(recipe_id)
    if result:
        return RecipeResponse(**result)
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Recipe not found"
    )


@app.get("/recipes/user/{user_id}", response_model=List[RecipeResponse])
async def get_user_recipes(user_id: int):
    """Get all custom recipes for a user"""
    results = recipe_crud.get_user_custom_recipes(user_id)
    if results is not None:
        return [RecipeResponse(**recipe) for recipe in results]
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="No recipes found for user"
    )


@app.get("/recipes/user/{user_id}/search")
async def search_recipes(user_id: int, search_term: str):
    """Search custom recipes by name or category"""
    results = recipe_crud.search_custom_recipes(user_id, search_term)
    return {"count": len(results), "recipes": results}


@app.get("/recipes/user/{user_id}/category/{category}")
async def get_recipes_by_category(user_id: int, category: str):
    """Get custom recipes by category"""
    results = recipe_crud.get_custom_recipes_by_category(user_id, category)
    return {"count": len(results), "recipes": results}


@app.get("/recipes/user/{user_id}/area/{area}")
async def get_recipes_by_area(user_id: int, area: str):
    """Get custom recipes by area (cuisine)"""
    results = recipe_crud.get_custom_recipes_by_area(user_id, area)
    return {"count": len(results), "recipes": results}


@app.put("/recipes/{recipe_id}")
async def update_recipe(recipe_id: int, recipe: RecipeUpdate):
    """Update a custom recipe"""
    # Only include non-None fields
    update_data = {k: v for k, v in recipe.dict().items() if v is not None}
    
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )
    
    # Validate recipe data
    is_valid, error_message = recipe_crud.validate_recipe_data(update_data)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_message
        )
    
    success = recipe_crud.update_custom_recipe(recipe_id, update_data)
    if success:
        return {"status": "success", "message": "Recipe updated"}
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Failed to update recipe"
    )


@app.delete("/recipes/{recipe_id}")
async def delete_recipe(recipe_id: int):
    """Delete a custom recipe"""
    success = recipe_crud.delete_custom_recipe(recipe_id)
    if success:
        return {"status": "success", "message": "Recipe deleted"}
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Failed to delete recipe"
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)

"""
Meal Proposer Service - REST API endpoints
"""
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from typing import Optional, List
from service import MealProposerService

app = FastAPI(title="Meal Proposer Service", version="1.0.0")

# Initialize service
meal_proposer = MealProposerService()


# Pydantic models
class MealProposalRequest(BaseModel):
    ingredient: Optional[str] = None


class MultipleMealsRequest(BaseModel):
    count: int = 3
    ingredient: Optional[str] = None


class RecipeResponse(BaseModel):
    id: int
    name: str
    category: str
    area: str
    instructions: str
    image: str
    tags: str
    youtube: str
    ingredients: List[dict]


# Endpoints
@app.get("/")
async def root():
    """Root endpoint"""
    return {"service": "Meal Proposer Service", "status": "running"}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.post("/propose", response_model=RecipeResponse)
async def propose_meal(request: MealProposalRequest):
    """Propose a single meal based on ingredient or randomly"""
    recipe = meal_proposer.propose_meal(request.ingredient)
    if recipe:
        return RecipeResponse(**meal_proposer.format_recipe(recipe))
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="No recipe found"
    )


@app.post("/propose/multiple", response_model=List[RecipeResponse])
async def propose_multiple_meals(request: MultipleMealsRequest):
    """Propose multiple meals"""
    recipes = meal_proposer.propose_multiple_meals(request.count, request.ingredient)
    if recipes:
        return [RecipeResponse(**meal_proposer.format_recipe(recipe)) for recipe in recipes]
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="No recipes found"
    )


@app.get("/recipe/{recipe_id}", response_model=RecipeResponse)
async def get_recipe_by_id(recipe_id: int):
    """Get a recipe by its ID"""
    recipe = meal_proposer.get_recipe_by_id(recipe_id)
    if recipe:
        return RecipeResponse(**meal_proposer.format_recipe(recipe))
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Recipe not found"
    )


@app.get("/search/ingredient/{ingredient}")
async def search_by_ingredient(ingredient: str):
    """Search for recipes by ingredient"""
    meals = meal_proposer.search_by_ingredient(ingredient)
    if meals:
        return {"count": len(meals), "meals": meals}
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="No recipes found with this ingredient"
    )


@app.get("/search/name/{name}")
async def search_by_name(name: str):
    """Search for recipes by name"""
    meals = meal_proposer.search_by_name(name)
    if meals:
        return {"count": len(meals), "meals": meals}
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="No recipes found with this name"
    )


@app.get("/random", response_model=RecipeResponse)
async def get_random_recipe():
    """Get a random recipe"""
    recipe = meal_proposer.get_random_recipe()
    if recipe:
        return RecipeResponse(**meal_proposer.format_recipe(recipe))
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="No recipe found"
    )


@app.get("/categories")
async def get_categories():
    """Get all meal categories"""
    categories = meal_proposer.get_all_categories()
    if categories:
        return {"count": len(categories), "categories": categories}
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="No categories found"
    )


@app.get("/filter/category/{category}")
async def filter_by_category(category: str):
    """Filter recipes by category"""
    meals = meal_proposer.filter_by_category(category)
    if meals:
        return {"count": len(meals), "meals": meals}
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="No recipes found in this category"
    )


@app.get("/areas")
async def get_areas():
    """Get all meal areas (cuisines)"""
    areas = meal_proposer.get_all_areas()
    if areas:
        return {"count": len(areas), "areas": areas}
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="No areas found"
    )


@app.get("/filter/area/{area}")
async def filter_by_area(area: str):
    """Filter recipes by area (cuisine)"""
    meals = meal_proposer.filter_by_area(area)
    if meals:
        return {"count": len(meals), "meals": meals}
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="No recipes found in this area"
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)

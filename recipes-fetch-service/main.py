"""
Recipes Fetch Service - REST API endpoints
"""
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from typing import Optional, List
from services import RecipesFetchService

app = FastAPI(title="Recipes Fetch Service", version="1.0.0")

# Initialize service
recipes_fetch = RecipesFetchService()


# Pydantic models
class RecipeResponse(BaseModel):
    name: str
    id_recipe: Optional[int] = None
    id_external: str
    is_external: bool

    category: Optional[str] = ""
    area: Optional[str] = ""
    instructions: Optional[str] = ""
    image: Optional[str] = ""
    tags: Optional[str] = ""
    youtube: Optional[str] = ""
    ingredients: Optional[List[dict]] = []


# Endpoints
@app.get("/")
async def root():
    """Root endpoint"""
    return {"service": "Recipes Fetch Service", "status": "running"}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.get("/search/name/{name}")
async def search_by_name(name: str):
    """Search for recipes by name"""
    meals = recipes_fetch.search_by_name(name)
    if meals:
        return {"count": len(meals), "meals": [recipes_fetch.format_recipe(m) for m in meals]}
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="No recipes found with this name"
    )


@app.get("/search/letter/{letter}")
async def search_by_letter(letter: str):
    """Search for recipes by first letter"""
    if len(letter) != 1:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Letter must be a single character")
    meals = recipes_fetch.search_by_first_letter(letter)
    if meals:
        return {"count": len(meals), "meals": [recipes_fetch.format_recipe(m) for m in meals]}
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No recipes found")


@app.get("/recipe/{recipe_id}", response_model=RecipeResponse)
async def get_recipe_by_id(recipe_id: int):
    """Get a recipe by its ID"""
    recipe = recipes_fetch.lookup_by_id(recipe_id)
    if recipe:
        return recipes_fetch.format_recipe(recipe)
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found")

@app.get("/lookup/{id}")
async def lookup_by_id_raw(id: str):
    """
    Get RAW details of a specific recipe by ID.
    Used by Interaction Service for Shadow Recipe import.
    """
    meal = recipes_fetch.lookup_by_id(id)
    if meal:
        return meal
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found")

@app.get("/random", response_model=RecipeResponse)
async def get_random_recipe():
    """Get a random recipe"""
    recipe = recipes_fetch.lookup_random()
    if recipe:
        return recipes_fetch.format_recipe(recipe)
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No recipe found")


@app.get("/random/{count}")
async def get_multiple_random_recipes(count: int):
    """Get multiple random recipes"""
    if count < 1 or count > 20:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Count must be between 1 and 20"
        )
    
    recipes = recipes_fetch.get_multiple_random_recipes(count)
    if recipes:
        return {"count": len(recipes), "recipes": [recipes_fetch.format_recipe(m) for m in recipes]}
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="No recipes found"
    )


@app.get("/categories")
async def get_categories():
    """Get all meal categories"""
    categories = recipes_fetch.list_all_categories()
    if categories:
        return {"count": len(categories), "categories": categories}
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="No categories found"
    )


@app.get("/filter/category/{category}")
async def filter_by_category(category: str):
    """Filter recipes by category"""
    meals = recipes_fetch.filter_by_category(category)
    if meals:
        return {"count": len(meals), "meals": [recipes_fetch.format_recipe(m) for m in meals]}
    raise HTTPException( status_code=status.HTTP_404_NOT_FOUND, detail="No recipes found in this category" )


@app.get("/areas")
async def get_areas():
    """Get all meal areas (cuisines)"""
    areas = recipes_fetch.list_all_areas()
    if areas:
        return {"count": len(areas), "areas": areas}
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No areas found" )


@app.get("/filter/area/{area}")
async def filter_by_area(area: str):
    """Filter recipes by area (cuisine)"""
    meals = recipes_fetch.filter_by_area(area)
    if meals:
        return {"count": len(meals), "meals": [recipes_fetch.format_recipe(m) for m in meals]}
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="No recipes found in this area"
    )


@app.get("/ingredients")
async def get_ingredients():
    """Get all ingredients"""
    ingredients = recipes_fetch.list_all_ingredients()
    if ingredients:
        return {"count": len(ingredients), "ingredients": ingredients}
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="No ingredients found"
    )


@app.get("/filter/ingredient/{ingredient}")
async def filter_by_ingredient(ingredient: str):
    """Filter recipes by ingredient"""
    meals = recipes_fetch.filter_by_ingredient(ingredient)
    if meals:
        return {"count": len(meals), "meals": [recipes_fetch.format_recipe(m) for m in meals]}
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="No recipes found with this ingredient"
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8006)

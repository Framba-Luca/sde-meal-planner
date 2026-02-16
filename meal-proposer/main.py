"""
Meal Proposer Service - REST API endpoints
"""
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from typing import Optional, List, Union
from service import MealProposerService
import random

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
    # Changed to str to support both Internal (int) and External (str) IDs uniformly
    id: str 
    name: str
    category: Optional[str] = "Unknown"
    area: Optional[str] = "Unknown"
    instructions: Optional[str] = ""
    image: Optional[str] = None
    tags: Optional[str] = ""
    youtube: Optional[str] = ""
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
    recipe = None
    
    if request.ingredient:
        candidates = meal_proposer.search_by_ingredient(request.ingredient)
        
        if candidates:
            selection = random.choice(candidates)
            recipe_id = selection.get("id")
            print(f"DEBUG: Selected candidate ID {recipe_id}, fetching full details...")
            
            recipe = meal_proposer.get_recipe_by_id(recipe_id)
            
    else:
        recipe = meal_proposer.get_random_meal()
    
    if recipe:
        return recipe
        
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="No meals found"
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
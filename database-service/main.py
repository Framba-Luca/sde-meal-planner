"""
Database Service - REST API endpoints
"""
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from typing import Optional, List
from datetime import date
from service import DatabaseService

app = FastAPI(title="Database Service", version="1.0.0")

# Initialize service
db_service = DatabaseService()


@app.on_event("startup")
async def startup_event():
    """Initialize database tables on startup"""
    print("Initializing database tables...")
    success = db_service.initialize_tables()
    if success:
        print("Database tables initialized successfully")
    else:
        print("Warning: Failed to initialize database tables")


# Pydantic models
class UserCreate(BaseModel):
    username: str
    hashed_password: str
    email: Optional[str] = None
    full_name: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    username: str
    full_name: str
    created_at: str


class MealPlanCreate(BaseModel):
    user_id: int
    start_date: date
    end_date: date


class MealPlanResponse(BaseModel):
    id: int
    user_id: int
    start_date: date
    end_date: date
    created_at: str


class MealPlanItemCreate(BaseModel):
    meal_plan_id: int
    mealdb_id: int
    meal_date: date
    meal_type: str


class MealPlanItemResponse(BaseModel):
    id: int
    meal_plan_id: int
    mealdb_id: int
    meal_date: date
    meal_type: str


class CustomRecipeCreate(BaseModel):
    user_id: int
    name: str
    category: Optional[str] = ""
    area: Optional[str] = ""
    instructions: Optional[str] = ""
    image: Optional[str] = ""
    tags: Optional[str] = ""


class CustomRecipeResponse(BaseModel):
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
    return {"service": "Database Service", "status": "running"}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.post("/init")
async def initialize_database():
    """Initialize database tables"""
    success = db_service.initialize_tables()
    if success:
        return {"status": "success", "message": "Database tables initialized"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initialize database tables"
        )


# User endpoints
@app.post("/users", response_model=UserResponse)
async def create_user(user: UserCreate):
    """Create a new user"""
    result = db_service.create_user(
        username=user.username,
        full_name=user.full_name,
        hashed_password=user.hashed_password
    )
    if result:
        return UserResponse(**result)
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Failed to create user"
    )


@app.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: int):
    """Get user by ID"""
    result = db_service.get_user_by_id(user_id)
    if result:
        return UserResponse(**result)
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="User not found"
    )


@app.get("/users/username/{username}")
async def get_user_by_username(username: str):
    """Get user by username (returns hashed_password for internal use)"""
    result = db_service.get_user_by_username(username)
    if result:
        return result
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="User not found"
    )


@app.get("/users", response_model=List[UserResponse])
async def get_all_users():
    """Get all users"""
    results = db_service.get_all_users()
    return [UserResponse(**user) for user in results]


@app.put("/users/{user_id}")
async def update_user(user_id: int, full_name: Optional[str] = None):
    """Update user information"""
    success = db_service.update_user(user_id, full_name)
    if success:
        return {"status": "success", "message": "User updated"}
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Failed to update user"
    )


@app.delete("/users/{user_id}")
async def delete_user(user_id: int):
    """Delete a user"""
    success = db_service.delete_user(user_id)
    if success:
        return {"status": "success", "message": "User deleted"}
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Failed to delete user"
    )


# Meal plan endpoints
@app.post("/meal-plans", response_model=MealPlanResponse)
async def create_meal_plan(meal_plan: MealPlanCreate):
    """Create a new meal plan"""
    result = db_service.create_meal_plan(meal_plan.user_id, meal_plan.start_date, meal_plan.end_date)
    if result:
        return MealPlanResponse(**result)
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Failed to create meal plan"
    )


@app.get("/meal-plans/{meal_plan_id}", response_model=MealPlanResponse)
async def get_meal_plan(meal_plan_id: int):
    """Get meal plan by ID"""
    result = db_service.get_meal_plan_by_id(meal_plan_id)
    if result:
        return MealPlanResponse(**result)
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Meal plan not found"
    )


@app.get("/meal-plans/user/{user_id}", response_model=List[MealPlanResponse])
async def get_meal_plans_by_user(user_id: int):
    """Get all meal plans for a user"""
    results = db_service.get_meal_plans_by_user(user_id)
    return [MealPlanResponse(**plan) for plan in results]


@app.delete("/meal-plans/{meal_plan_id}")
async def delete_meal_plan(meal_plan_id: int):
    """Delete a meal plan"""
    success = db_service.delete_meal_plan(meal_plan_id)
    if success:
        return {"status": "success", "message": "Meal plan deleted"}
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Failed to delete meal plan"
    )


# Meal plan item endpoints
@app.post("/meal-plan-items", response_model=MealPlanItemResponse)
async def add_meal_plan_item(item: MealPlanItemCreate):
    """Add a meal to a meal plan"""
    result = db_service.add_meal_plan_item(item.meal_plan_id, item.mealdb_id, item.meal_date, item.meal_type)
    if result:
        return MealPlanItemResponse(**result)
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Failed to add meal plan item"
    )


@app.get("/meal-plan-items/{meal_plan_id}", response_model=List[MealPlanItemResponse])
async def get_meal_plan_items(meal_plan_id: int):
    """Get all items in a meal plan"""
    results = db_service.get_meal_plan_items(meal_plan_id)
    return [MealPlanItemResponse(**item) for item in results]


@app.get("/meal-plan-items/{meal_plan_id}/{meal_date}", response_model=List[MealPlanItemResponse])
async def get_meal_plan_items_by_date(meal_plan_id: int, meal_date: date):
    """Get meal plan items for a specific date"""
    results = db_service.get_meal_plan_items_by_date(meal_plan_id, meal_date)
    return [MealPlanItemResponse(**item) for item in results]


@app.put("/meal-plan-items/{item_id}")
async def update_meal_plan_item(item_id: int, mealdb_id: Optional[int] = None, meal_type: Optional[str] = None):
    """Update a meal plan item"""
    success = db_service.update_meal_plan_item(item_id, mealdb_id, meal_type)
    if success:
        return {"status": "success", "message": "Meal plan item updated"}
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Failed to update meal plan item"
    )


@app.delete("/meal-plan-items/{item_id}")
async def delete_meal_plan_item(item_id: int):
    """Delete a meal plan item"""
    success = db_service.delete_meal_plan_item(item_id)
    if success:
        return {"status": "success", "message": "Meal plan item deleted"}
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Failed to delete meal plan item"
    )


# Custom recipe endpoints
@app.post("/custom-recipes", response_model=CustomRecipeResponse)
async def create_custom_recipe(recipe: CustomRecipeCreate):
    """Create a custom recipe"""
    result = db_service.create_custom_recipe(recipe.user_id, recipe.dict())
    if result:
        return CustomRecipeResponse(**result)
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Failed to create custom recipe"
    )


@app.get("/custom-recipes/{recipe_id}", response_model=CustomRecipeResponse)
async def get_custom_recipe(recipe_id: int):
    """Get custom recipe by ID"""
    result = db_service.get_custom_recipe_by_id(recipe_id)
    if result:
        return CustomRecipeResponse(**result)
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Custom recipe not found"
    )


@app.get("/custom-recipes/user/{user_id}", response_model=List[CustomRecipeResponse])
async def get_custom_recipes_by_user(user_id: int):
    """Get all custom recipes for a user"""
    results = db_service.get_custom_recipes_by_user(user_id)
    return [CustomRecipeResponse(**recipe) for recipe in results]


@app.put("/custom-recipes/{recipe_id}")
async def update_custom_recipe(recipe_id: int, recipe_data: dict):
    """Update a custom recipe"""
    success = db_service.update_custom_recipe(recipe_id, recipe_data)
    if success:
        return {"status": "success", "message": "Custom recipe updated"}
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Failed to update custom recipe"
    )


@app.delete("/custom-recipes/{recipe_id}")
async def delete_custom_recipe(recipe_id: int):
    """Delete a custom recipe"""
    success = db_service.delete_custom_recipe(recipe_id)
    if success:
        return {"status": "success", "message": "Custom recipe deleted"}
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Failed to delete custom recipe"
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)

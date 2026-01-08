"""
Streamlit GUI - Main interface for the Meal Planner application
"""
import streamlit as st
import requests
from datetime import date, timedelta
import os

# Service URLs
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://authentication-service:8001")
DATABASE_SERVICE_URL = os.getenv("DATABASE_SERVICE_URL", "http://database-service:8002")
MEAL_PROPOSER_URL = os.getenv("MEAL_PROPOSER_URL", "http://meal-proposer:8003")
MEAL_PLANNER_URL = os.getenv("MEAL_PLANNER_URL", "http://meal-planner-pcl:8004")
RECIPE_CRUD_URL = os.getenv("RECIPE_CRUD_URL", "http://recipe-crud-interaction:8005")
RECIPES_FETCH_URL = os.getenv("RECIPES_FETCH_URL", "http://recipes-fetch-service:8006")

# Page configuration
st.set_page_config(
    page_title="Meal Planner",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="expanded"
)


# Helper functions
def make_request(url, method="GET", data=None):
    """Make HTTP request to a service"""
    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data)
        elif method == "PUT":
            response = requests.put(url, json=data)
        elif method == "DELETE":
            response = requests.delete(url)
        else:
            return None
        
        if response.status_code == 200:
            return response.json()
        return None
    except requests.RequestException as e:
        st.error(f"Error: {e}")
        return None


def initialize_session_state():
    """Initialize session state variables"""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "user" not in st.session_state:
        st.session_state.user = None
    if "token" not in st.session_state:
        st.session_state.token = None


# Authentication functions
def login_page():
    """Display login page"""
    st.title("🍽️ Meal Planner")
    st.subheader("Login")
    
    tab1, tab2, tab3 = st.tabs(["Login", "Register", "Google OAuth"])
    
    with tab1:
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        
        if st.button("Login"):
            data = {"username": username, "password": password}
            result = make_request(f"{AUTH_SERVICE_URL}/token", method="POST", data=data)
            
            if result:
                st.session_state.authenticated = True
                st.session_state.token = result["access_token"]
                st.session_state.user = result["user"]
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("Invalid username or password")
    
    with tab2:
        st.subheader("Create Account")
        reg_username = st.text_input("Username", key="reg_username")
        reg_password = st.text_input("Password", type="password", key="reg_password")
        reg_full_name = st.text_input("Full Name (optional)", key="reg_full_name")
        
        if st.button("Register"):
            if not reg_username or not reg_password:
                st.error("Username and password are required")
            else:
                data = {
                    "username": reg_username,
                    "password": reg_password,
                    "full_name": reg_full_name if reg_full_name else None
                }
                result = make_request(f"{AUTH_SERVICE_URL}/register", method="POST", data=data)
                
                if result:
                    st.success("Account created successfully! Please login.")
                else:
                    st.error("Failed to create account. Username may already exist.")
    
    with tab3:
        if st.button("Login with Google"):
            # In a real implementation, this would redirect to Google OAuth
            st.info("Google OAuth integration requires proper setup. Please use username/password for now.")


def logout():
    """Logout user"""
    st.session_state.authenticated = False
    st.session_state.user = None
    st.session_state.token = None
    st.rerun()


# Main application pages
def meal_proposal_page():
    """Meal proposal page"""
    st.header("🍲 Meal Proposal")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        ingredient = st.text_input("Ingredient (optional)")
        if st.button("Propose Meal"):
            data = {"ingredient": ingredient} if ingredient else {}
            result = make_request(f"{MEAL_PROPOSER_URL}/propose", method="POST", data=data)
            
            if result:
                st.session_state.proposed_meal = result
            else:
                st.error("Failed to propose meal")
    
    with col2:
        if "proposed_meal" in st.session_state and st.session_state.proposed_meal:
            meal = st.session_state.proposed_meal
            st.subheader(meal["name"])
            
            col_img, col_info = st.columns([1, 2])
            
            with col_img:
                if meal["image"]:
                    st.image(meal["image"], use_column_width=True)
            
            with col_info:
                st.write(f"**Category:** {meal['category']}")
                st.write(f"**Area:** {meal['area']}")
                st.write(f"**Tags:** {meal['tags']}")
                
                st.write("**Ingredients:**")
                for ing in meal["ingredients"]:
                    st.write(f"- {ing['ingredient']}: {ing['measure']}")
                
                st.write("**Instructions:**")
                st.write(meal["instructions"])


def meal_planning_page():
    """Meal planning page"""
    st.header("📅 Meal Planning")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        num_days = st.number_input("Number of Days", min_value=1, max_value=30, value=7)
        start_date = st.date_input("Start Date", value=date.today())
        ingredient = st.text_input("Ingredient (optional)")
        
        if st.button("Generate Meal Plan"):
            data = {
                "user_id": st.session_state.user["username"],
                "num_days": num_days,
                "start_date": start_date.isoformat(),
                "ingredient": ingredient if ingredient else None
            }
            result = make_request(f"{MEAL_PLANNER_URL}/meal-plans/generate", method="POST", data=data)
            
            if result:
                st.session_state.current_meal_plan = result
                st.success("Meal plan generated successfully!")
            else:
                st.error("Failed to generate meal plan")
    
    with col2:
        if "current_meal_plan" in st.session_state and st.session_state.current_meal_plan:
            meal_plan = st.session_state.current_meal_plan
            
            st.subheader(f"Meal Plan: {meal_plan['start_date']} to {meal_plan['end_date']}")
            
            for day_date, meals in meal_plan["days"].items():
                st.write(f"### 📆 {day_date}")
                
                col_breakfast, col_lunch, col_dinner = st.columns(3)
                
                with col_breakfast:
                    st.write("**Breakfast**")
                    if "breakfast" in meals:
                        meal = meals["breakfast"]["recipe"]
                        st.write(meal["name"])
                        if meal["image"]:
                            st.image(meal["image"], use_column_width=True)
                
                with col_lunch:
                    st.write("**Lunch**")
                    if "lunch" in meals:
                        meal = meals["lunch"]["recipe"]
                        st.write(meal["name"])
                        if meal["image"]:
                            st.image(meal["image"], use_column_width=True)
                
                with col_dinner:
                    st.write("**Dinner**")
                    if "dinner" in meals:
                        meal = meals["dinner"]["recipe"]
                        st.write(meal["name"])
                        if meal["image"]:
                            st.image(meal["image"], use_column_width=True)


def recipe_interaction_page():
    """Recipe interaction page"""
    st.header("📝 My Recipes")
    
    tab1, tab2 = st.tabs(["View Recipes", "Add Recipe"])
    
    with tab1:
        # View user's custom recipes
        result = make_request(f"{RECIPE_CRUD_URL}/recipes/user/{st.session_state.user['username']}")
        
        if result:
            recipes = result
            if recipes:
                for recipe in recipes:
                    with st.expander(f"{recipe['name']}"):
                        st.write(f"**Category:** {recipe['category']}")
                        st.write(f"**Area:** {recipe['area']}")
                        st.write(f"**Tags:** {recipe['tags']}")
                        st.write("**Instructions:**")
                        st.write(recipe['instructions'])
            else:
                st.info("No custom recipes found. Add your first recipe!")
        else:
            st.error("Failed to fetch recipes")
    
    with tab2:
        # Add new recipe
        st.subheader("Add New Recipe")
        
        name = st.text_input("Recipe Name *")
        category = st.text_input("Category")
        area = st.text_input("Area/Cuisine")
        instructions = st.text_area("Instructions", height=200)
        image = st.text_input("Image URL")
        tags = st.text_input("Tags (comma-separated)")
        
        if st.button("Save Recipe"):
            if not name:
                st.error("Recipe name is required")
            else:
                data = {
                    "user_id": st.session_state.user["username"],
                    "name": name,
                    "category": category,
                    "area": area,
                    "instructions": instructions,
                    "image": image,
                    "tags": tags
                }
                
                result = make_request(f"{RECIPE_CRUD_URL}/recipes", method="POST", data=data)
                
                if result:
                    st.success("Recipe saved successfully!")
                    st.rerun()
                else:
                    st.error("Failed to save recipe")


def recipe_search_page():
    """Recipe search page"""
    st.header("🔍 Recipe Search")
    
    search_type = st.selectbox("Search By", ["Name", "Ingredient", "Category", "Area"])
    
    if search_type == "Name":
        search_term = st.text_input("Recipe Name")
        if st.button("Search"):
            result = make_request(f"{RECIPES_FETCH_URL}/search/name/{search_term}")
            if result and result["meals"]:
                for meal in result["meals"]:
                    st.write(f"### {meal['strMeal']}")
                    st.write(f"Category: {meal['strCategory']}, Area: {meal['strArea']}")
                    if meal['strMealThumb']:
                        st.image(meal['strMealThumb'], width=200)
            else:
                st.info("No recipes found")
    
    elif search_type == "Ingredient":
        search_term = st.text_input("Ingredient")
        if st.button("Search"):
            result = make_request(f"{RECIPES_FETCH_URL}/filter/ingredient/{search_term}")
            if result and result["meals"]:
                for meal in result["meals"]:
                    st.write(f"### {meal['strMeal']}")
                    st.write(f"Category: {meal['strCategory']}, Area: {meal['strArea']}")
                    if meal['strMealThumb']:
                        st.image(meal['strMealThumb'], width=200)
            else:
                st.info("No recipes found")
    
    elif search_type == "Category":
        categories = make_request(f"{RECIPES_FETCH_URL}/categories")
        if categories:
            category_names = [cat["strCategory"] for cat in categories["categories"]]
            selected_category = st.selectbox("Select Category", category_names)
            
            if st.button("Search"):
                result = make_request(f"{RECIPES_FETCH_URL}/filter/category/{selected_category}")
                if result and result["meals"]:
                    for meal in result["meals"]:
                        st.write(f"### {meal['strMeal']}")
                        st.write(f"Category: {meal['strCategory']}, Area: {meal['strArea']}")
                        if meal['strMealThumb']:
                            st.image(meal['strMealThumb'], width=200)
                else:
                    st.info("No recipes found")
    
    elif search_type == "Area":
        areas = make_request(f"{RECIPES_FETCH_URL}/areas")
        if areas:
            area_names = [area["strArea"] for area in areas["areas"]]
            selected_area = st.selectbox("Select Area", area_names)
            
            if st.button("Search"):
                result = make_request(f"{RECIPES_FETCH_URL}/filter/area/{selected_area}")
                if result and result["meals"]:
                    for meal in result["meals"]:
                        st.write(f"### {meal['strMeal']}")
                        st.write(f"Category: {meal['strCategory']}, Area: {meal['strArea']}")
                        if meal['strMealThumb']:
                            st.image(meal['strMealThumb'], width=200)
                else:
                    st.info("No recipes found")


def my_meal_plans_page():
    """View user's meal plans"""
    st.header("📋 My Meal Plans")
    
    result = make_request(f"{MEAL_PLANNER_URL}/meal-plans/user/{st.session_state.user['username']}")
    
    if result and result["meal_plans"]:
        for plan in result["meal_plans"]:
            with st.expander(f"Plan: {plan['start_date']} to {plan['end_date']}"):
                st.write(f"**Plan ID:** {plan['id']}")
                st.write(f"**Created:** {plan['created_at']}")
                
                # Get meal plan items
                items = make_request(f"{MEAL_PLANNER_URL}/meal-plans/{plan['id']}/items")
                if items and items["items"]:
                    st.write("**Meals:**")
                    for item in items["items"]:
                        st.write(f"- {item['meal_date']}: {item['meal_type']} (Recipe ID: {item['mealdb_id']})")
                
                if st.button(f"Delete Plan {plan['id']}", key=f"delete_{plan['id']}"):
                    make_request(f"{MEAL_PLANNER_URL}/meal-plans/{plan['id']}", method="DELETE")
                    st.success("Meal plan deleted!")
                    st.rerun()
    else:
        st.info("No meal plans found. Create your first meal plan!")


# Main application
def main():
    """Main application function"""
    initialize_session_state()
    
    # Sidebar
    with st.sidebar:
        st.title("🍽️ Meal Planner")
        
        if st.session_state.authenticated:
            st.write(f"Welcome, {st.session_state.user['full_name']}!")
            st.button("Logout", on_click=logout)
            
            st.divider()
            
            page = st.radio(
                "Navigate",
                ["Meal Proposal", "Meal Planning", "My Recipes", "Recipe Search", "My Meal Plans"]
            )
        else:
            page = "Login"
    
    # Main content
    if not st.session_state.authenticated:
        login_page()
    else:
        if page == "Meal Proposal":
            meal_proposal_page()
        elif page == "Meal Planning":
            meal_planning_page()
        elif page == "My Recipes":
            recipe_interaction_page()
        elif page == "Recipe Search":
            recipe_search_page()
        elif page == "My Meal Plans":
            my_meal_plans_page()


if __name__ == "__main__":
    main()

"""
Streamlit GUI - Main interface for the Meal Planner application
"""
import streamlit as st
import extra_streamlit_components as stx
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
def make_request(url, method="GET", data=None, use_form_data=False):
    """Make HTTP request to a service"""
    headers = {}

    if st.session_state.authenticated and st.session_state.token:
        headers["Authorization"] = f"Bearer {st.session_state.token}"

    assert not use_form_data or method == "POST", "use_form_data is only valid for POST requests"

    try:
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            # CHANGE: Corretto passaggio parametri.
            if use_form_data:
                # Content-Type: application/x-www-form-urlencoded
                response = requests.post(url, data=data, headers=headers)
            else:
                # Content-Type: application/json
                response = requests.post(url, json=data, headers=headers)
        elif method == "PUT":
            response = requests.put(url, json=data, headers=headers)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers)
        else:
            return None
        
        # Gestione risposte
        if response.status_code in [200, 201]:
            return response.json()
        elif response.status_code == 401:
            st.error("Session expired or unauthorized. Please login again.")
            st.session_state.authenticated = False
            st.session_state.user = None
            st.rerun()
        elif response.status_code == 403:
            st.error("Access denied. You do not have permission to perform this action.")
        elif response.status_code == 422:
            # Mostra errore dettagliato dal backend per debug
            try:
                detail = response.json().get('detail')
                st.error(f"Validation Error (422): {detail}")
            except:
                st.error(f"Validation Error (422): {response.text}")
            
        return None
    except requests.RequestException as e:
        st.error(f"Error: {e}")
        return None

@st.cache_resource(experimental_allow_widgets=True)
def get_cookie_manager():
    return stx.CookieManager()

cookie_manager = get_cookie_manager()

def initialize_session_state():
    """Initialize session state variables"""
    
    # 1. Retrieves the token from cookies (if any)
    cookie_token = cookie_manager.get(cookie="access_token")
    
    # Initialize the session if doesn't
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "token" not in st.session_state:
        st.session_state.token = None
    if "user" not in st.session_state:
        st.session_state.user = None
    if "user_id" not in st.session_state:
        st.session_state.user_id = None

    # Case A: We have a saved cookie -> Autologin
    if cookie_token and not st.session_state.authenticated:
        st.session_state.token = cookie_token
        st.session_state.authenticated = True
        # Nota: Qui user è generico perché nel cookie abbiamo solo il token.
        # Idealmente dovresti fare una chiamata /me al backend per avere i dettagli aggiornati.
        if not st.session_state.user:
             st.session_state.user = {"username": "User", "full_name": "Welcome Back"}

    # Case B: Google Login (Token in the URL)
    try:
        query_params = st.query_params
    except AttributeError:
        query_params = st.experimental_get_query_params()

    if "access_token" in query_params:
        val = query_params["access_token"]
        token = val[0] if isinstance(val, list) else val
        
        user_val = query_params.get("username", "User")
        username = user_val[0] if isinstance(user_val, list) else user_val
        
        full_name_val = query_params.get("full_name", "")
        full_name = full_name_val[0] if isinstance(full_name_val, list) else full_name_val

        # Save in Session State
        st.session_state.token = token
        st.session_state.user = {
            "username": username,
            "full_name": full_name
        }
        st.session_state.authenticated = True
        
        # Fetch user ID from database service
        fetched_correctly = fetch_user_id(username)
        
        if fetched_correctly:
            # --- Save in the Cookie ---
            cookie_manager.set("access_token", token, key="google_auth_token")
            # -----------------------------------------------

            # Clean the URL to remove token parameters
            try:
                st.query_params.clear()
            except AttributeError:
                st.experimental_set_query_params()
            
            # Refresh to have the updated state
            st.rerun()
        else:
            # Clear authentication state if user ID cannot be fetched
            st.session_state.authenticated = False
            st.session_state.token = None
            st.session_state.user = None
            st.session_state.user_id = None
            st.error("Login failed: Unable to fetch user ID. User may not exist in the database.")

# Authentication functions
def fetch_user_id(username):
    """Fetch user ID from database service
    
    Returns:
        bool: True if user ID was fetched successfully, False otherwise
    """
    result = make_request(f"{DATABASE_SERVICE_URL}/api/v1/users/username/{username}")
    if result and "id" in result:
        st.session_state.user_id = result["id"]
        return True
    return False

def login_page():
    """Display login page"""
    st.title("🍽️ Meal Planner")
    st.subheader("Login")
    
    tab1, tab2, tab3 = st.tabs(["Login", "Register", "Google OAuth"])
    
    with tab1:
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        
        if st.button("Login"):
            if not username or not password:
                st.warning("Please enter username and password")
            else:
                data = {"username": username, "password": password}
                
                # FIX: Cambiato a use_form_data=False (default) per inviare JSON.
                # L'errore 422 indicava che il backend si aspettava un oggetto (dict), non una stringa form-data.
                result = make_request(f"{AUTH_SERVICE_URL}/api/v1/auth/login", method="POST", data=data, use_form_data=True)
                
                if result:
                    st.session_state.authenticated = True
                    st.session_state.token = result["access_token"]
                    st.session_state.user = result["user"]
                    # Fetch user ID from database service
                    fetched_correctly = fetch_user_id(username)
                    
                    if fetched_correctly:
                        st.success("Login successful!")
                        cookie_manager.set("access_token", result["access_token"], key="login_token")
                        st.rerun()
                    else:
                        # Clear authentication state if user ID cannot be fetched
                        st.session_state.authenticated = False
                        st.session_state.token = None
                        st.session_state.user = None
                        st.session_state.user_id = None
                        st.error("Login failed: Unable to fetch user ID. User may not exist in the database.")
    
    with tab2:
        st.subheader("Create Account")
        reg_username = st.text_input("Username", key="reg_username")
        reg_password = st.text_input("Password", type="password", key="reg_password")
        reg_full_name = st.text_input("Full Name (optional)", key="reg_full_name")
        reg_email = st.text_input("Email (optional)", key="reg_email")
        
        if st.button("Register"):
            if not reg_username or not reg_password:
                st.error("Username and password are required")
            else:
                data = {
                    "username": reg_username,
                    "password": reg_password,
                    "full_name": reg_full_name if reg_full_name else None,
                    "email": reg_email if reg_email else None
                }
                # La registrazione usa JSON
                result = make_request(f"{AUTH_SERVICE_URL}/api/v1/auth/register", method="POST", data=data)
                
                if result:
                    st.success("Account created successfully! Please login.")
                else:
                    st.error("Failed to create account. Username may already exist.")
    
    with tab3:
        st.subheader("Google Login")
        if st.button("Login with Google"):
            try:
                # 1. Streamlit asks backend for Google URL
                response = requests.get(f"{AUTH_SERVICE_URL}/api/v1/auth/google/login", timeout=5, allow_redirects=False)
                
                if response.status_code == 307:  # Redirect status
                    google_auth_url = response.headers.get("location")
                    if google_auth_url:
                        st.link_button(
                            label="Continue to Google", 
                            url=google_auth_url, 
                            type="primary",
                            use_container_width=True
                        )
                    else:
                        st.error("Invalid authentication URL.")
                else:
                    st.error(f"Backend communication error: {response.status_code}")
                
            except requests.exceptions.ConnectionError:
                st.error("Cannot contact authentication service.")
            except Exception as e:
                st.error(f"Error: {e}")

def logout():
    """Logout user"""
    cookie_manager.delete("access_token")
    st.session_state.authenticated = False
    st.session_state.user = None
    st.session_state.user_id = None
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
            if not st.session_state.user_id:
                st.error("User ID not found. Please login again.")
            else:
                data = {
                    "user_id": st.session_state.user_id,
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
        if not st.session_state.user_id:
            st.error("User ID not found. Please login again.")
        else:
            result = make_request(f"{RECIPE_CRUD_URL}/recipes/user/{st.session_state.user_id}")
        
        if result is not None:
            recipes = result
            if recipes and len(recipes) > 0:
                for recipe in recipes:
                    with st.expander(f"{recipe['name']}"):
                        col1, col2 = st.columns([3, 1])
                        
                        with col1:
                            st.write(f"**Category:** {recipe.get('category', 'N/A')}")
                            st.write(f"**Area:** {recipe.get('area', 'N/A')}")
                            st.write(f"**Tags:** {recipe.get('tags', 'N/A')}")
                            st.write("**Instructions:**")
                            instructions = recipe.get('instructions', 'No instructions provided')
                            if instructions:
                                st.write(instructions)
                            else:
                                st.write("No instructions provided")
                        
                        with col2:
                            if st.button("🗑️ Delete", key=f"delete_{recipe['id']}", type="secondary"):
                                delete_result = make_request(
                                    f"{RECIPE_CRUD_URL}/recipes/{recipe['id']}",
                                    method="DELETE"
                                )
                                if delete_result:
                                    st.success("Recipe deleted successfully!")
                                    st.rerun()
                                else:
                                    st.error("Failed to delete recipe")
            else:
                st.info("🍽️ **No custom recipes found!**")
                st.write("Start by adding your first recipe in the 'Add Recipe' tab above.")
                st.write("You can create recipes with:")
                st.write("- Recipe name (required)")
                st.write("- Category and cuisine area")
                st.write("- Detailed instructions")
                st.write("- Image URL")
                st.write("- Tags for easy searching")
        else:
            st.error("❌ Failed to fetch recipes. Please try again later.")
    
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
                if not st.session_state.user_id:
                    st.error("User ID not found. Please login again.")
                else:
                    data = {
                        "user_id": st.session_state.user_id,
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
    
    if not st.session_state.user_id:
        st.error("User ID not found. Please login again.")
    else:
        result = make_request(f"{MEAL_PLANNER_URL}/meal-plans/user/{st.session_state.user_id}")
    
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
"""
Streamlit GUI - Main Entry Point
"""
import streamlit as st
from modules.auth import initialize_session_state, logout
from modules.views.login import render_login_page
from modules.views.meal_proposal import render_meal_proposal
from modules.views.meal_planning import render_meal_planning
from modules.views.my_recipes import render_recipe_interaction
from modules.views.recipe_search import render_recipe_search
from modules.views.my_plans import render_my_meal_plans

# Page Configuration
st.set_page_config(
    page_title="Meal Planner",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    # 1. Initialize Session and Authentication State
    initialize_session_state()
    
    # 2. Sidebar Navigation
    with st.sidebar:
        st.title("🍽️ Meal Planner")
        
        if st.session_state.authenticated:
            # Show user info if logged in
            user_name = st.session_state.user.get('full_name', 'User')
            st.write(f"Welcome, {user_name}!")
            st.button("Logout", on_click=logout, type="primary")
            
            st.divider()
            
            # Navigation Menu
            selection = st.radio(
                "Navigate",
                ["Meal Proposal", "Meal Planning", "My Recipes", "Recipe Search", "My Meal Plans"]
            )
        else:
            selection = "Login"

    # 3. Page Routing
    if not st.session_state.authenticated:
        render_login_page()
    else:
        if selection == "Meal Proposal":
            render_meal_proposal()
        elif selection == "Meal Planning":
            render_meal_planning() 
        elif selection == "My Recipes":
            render_recipe_interaction()
        elif selection == "Recipe Search":
            render_recipe_search()
        elif selection == "My Meal Plans":
            render_my_meal_plans()

if __name__ == "__main__":
    main()
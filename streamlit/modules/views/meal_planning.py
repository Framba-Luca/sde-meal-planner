import streamlit as st
from datetime import date
from modules.config import MEAL_PLANNER_URL
from modules.api import make_request

def render_meal_planning():
    """
    Renders the page to generate a new meal plan.
    """
    st.header("📅 Meal Planning")
    
    col1, col2 = st.columns([1, 2])
    
    # --- Left Column: Input Form ---
    with col1:
        with st.container(border=True):
            st.subheader("Generate New Plan")
            num_days = st.number_input("Number of Days", min_value=1, max_value=30, value=7)
            start_date = st.date_input("Start Date", value=date.today())
            ingredient = st.text_input("Preferred Ingredient (optional)", placeholder="e.g. Chicken")
            
            if st.button("Generate Plan", type="primary"):
                user_id = st.session_state.get("user_id")
                
                if not user_id:
                    st.error("User ID not found. Please login again.")
                else:
                    with st.spinner("Generating your meal plan..."):
                        payload = {
                            "user_id": user_id,
                            "num_days": num_days,
                            "start_date": start_date.isoformat(),
                            "ingredient": ingredient if ingredient else None
                        }
                        # Call the Meal Planner Service
                        result = make_request(f"{MEAL_PLANNER_URL}/meal-plans/generate", method="POST", data=payload)
                    
                    if result:
                        st.session_state.current_meal_plan = result
                        st.success("Meal plan generated and saved successfully!")
                    else:
                        st.error("Failed to generate meal plan. The service might be busy.")
    
    # --- Right Column: Plan Visualization ---
    with col2:
        if "current_meal_plan" in st.session_state and st.session_state.current_meal_plan:
            display_meal_plan(st.session_state.current_meal_plan)
        else:
            st.info("👈 Use the form on the left to generate a personalized meal plan.")

def display_meal_plan(meal_plan):
    """
    Helper function to display the meal plan details.
    """
    st.subheader(f"Plan: {meal_plan.get('start_date')} to {meal_plan.get('end_date')}")
    st.caption(f"Plan ID: {meal_plan.get('meal_plan_id')} (Saved in database)")
    
    # Iterate through days (ensure it handles dict correctly)
    days = meal_plan.get("days", {})
    
    for day_date, meals in days.items():
        with st.expander(f"📆 {day_date}", expanded=True):
            c_brk, c_lun, c_din = st.columns(3)
            
            _render_meal_slot(c_brk, "Breakfast", meals.get("breakfast"))
            _render_meal_slot(c_lun, "Lunch", meals.get("lunch"))
            _render_meal_slot(c_din, "Dinner", meals.get("dinner"))

def _render_meal_slot(column, title, meal_data):
    """
    Renders a single meal slot (e.g., Breakfast) within a column.
    """
    with column:
        st.markdown(f"**{title}**")
        if meal_data and "recipe" in meal_data:
            recipe = meal_data["recipe"]
            st.write(recipe.get("name", "Unknown"))
            img = recipe.get("image")
            if img:
                st.image(img, width=300)
        else:
            st.caption("No meal planned")
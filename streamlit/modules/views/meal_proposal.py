import streamlit as st
from modules.config import MEAL_PROPOSER_URL
from modules.api import make_request
from modules.utils import get_ingredients_list

def render_meal_proposal():
    st.header("🍲 Meal Proposal")
    col1, col2 = st.columns([1, 2])
    
    with col1:
        ingredient = st.text_input("Ingredient (optional)")
        if st.button("Propose Meal"):
            data = {"ingredient": ingredient} if ingredient else {}
            res = make_request(f"{MEAL_PROPOSER_URL}/propose", method="POST", data=data)
            if res:
                st.session_state.proposed_meal = res

    with col2:
        if st.session_state.get("proposed_meal"):
            show_meal_details(st.session_state.proposed_meal)

def show_meal_details(meal):
    """
    Visualizes the data of a meal proposal in a user-friendly format.
    """
    
    # --- DEBUG (Opzionale: removes during production) ---
    with st.expander("🔍 Debug Raw JSON"):
        st.json(meal)
    # ------------------------------------------------

    # 1. Name
    title = meal.get("name") or meal.get("strMeal") or "Unknown Meal"
    st.subheader(f"🍲 {title}")

    col1, col2 = st.columns([1, 2])

    with col1:
        # 2. Image
        image_url = meal.get("image") or meal.get("strMealThumb")
        if image_url:
            st.image(image_url, use_container_width=True)
        else:
            st.info("No Image")

    with col2:
        # 3. Category & Area
        category = meal.get("category") or meal.get("strCategory") or "N/A"
        area = meal.get("area") or meal.get("strArea") or "N/A"

        st.markdown(f"**📂 Category:** {category}")
        st.markdown(f"**🌍 Area:** {area}")
        
        # 4. Ingredients
        st.markdown("### 🛒 Ingredients")
        formatted_ingredients = get_ingredients_list(meal)
        
        if formatted_ingredients:
            for item in formatted_ingredients:
                st.markdown(item)
        else:
            st.warning("No ingredients data found.")

    # 5. Instructions
    st.markdown("### 📝 Instructions")
    instructions = meal.get("instructions") or meal.get("strInstructions")
    if instructions:
        st.write(instructions)
    else:
        st.markdown("No instructions provided.")
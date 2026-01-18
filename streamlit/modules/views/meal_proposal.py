import streamlit as st
from modules.config import MEAL_PROPOSER_URL
from modules.api import make_request

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
    st.subheader(meal["name"])
    c_img, c_info = st.columns([1, 2])
    with c_img:
        if meal.get("image"): st.image(meal["image"], width=300)
    with c_info:
        st.write(f"**Category:** {meal.get('category')}")
        st.write(f"**Area:** {meal.get('area')}")
        st.write("**Ingredients:**")
        for ing in meal.get("ingredients", []):
            st.write(f"- {ing['ingredient']}: {ing['measure']}")
    st.write("**Instructions:**")
    st.write(meal.get("instructions"))
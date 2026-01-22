import streamlit as st
from modules.config import RECIPE_CRUD_URL, API_VERSION
from modules.api import make_request

recipe_url = (f"{RECIPE_CRUD_URL}/{API_VERSION}") 

def render_recipe_interaction():
    """
    Main page for user's custom recipes (View / Add).
    """

    st.header("📝 My Recipes")
    
    tab1, tab2 = st.tabs(["View Recipes", "Add Recipe"])
    
    with tab1:
        _render_view_recipes_tab()
    
    with tab2:
        _render_add_recipe_tab()

def _render_view_recipes_tab():
    """
    Logic for fetching and displaying the list of recipes.
    """
    user_id = st.session_state.get("user_id")
    if not user_id:
        st.error("Session Error: User ID missing. Please login.")
        return

    # Fetch recipes from CRUD Service
    recipes = make_request(f"{recipe_url}/recipes/user/{user_id}")
    
    if recipes:
        for recipe in recipes:
            with st.expander(f"🥘 {recipe['name']}"):
                c1, c2 = st.columns([3, 1])
                
                with c1:
                    st.caption(f"Category: {recipe.get('category', '-')} | Area: {recipe.get('area', '-')}")
                    st.write(f"**Tags:** {recipe.get('tags', '-')}")
                    st.markdown("**Instructions:**")
                    st.write(recipe.get('instructions', 'No instructions provided.'))
                    if recipe.get("image"):
                        st.image(recipe["image"], width=200)

                with c2:
                    st.write("Actions")
                    # Delete Button
                    if st.button("🗑️ Delete", key=f"del_rec_{recipe['id']}", type="secondary"):
                        if make_request(f"{recipe_url}/recipes/{recipe['id']}", method="DELETE"):
                            st.success("Deleted!")
                            st.rerun()
    else:
        st.info("You haven't saved any custom recipes yet.")
        st.write("Go to the 'Add Recipe' tab to create one.")

def _render_add_recipe_tab():
    """
    Logic for the 'Add New Recipe' form.
    """
    st.subheader("Add New Recipe")
    
    with st.form("add_recipe_form"):
        name = st.text_input("Recipe Name *")
        c1, c2 = st.columns(2)
        with c1:
            category = st.text_input("Category")
            image = st.text_input("Image URL")
        with c2:
            area = st.text_input("Area/Cuisine")
            tags = st.text_input("Tags (comma-separated)")
            
        instructions = st.text_area("Instructions", height=150)
        
        submitted = st.form_submit_button("Save Recipe")
        
        if submitted:
            if not name:
                st.error("Recipe name is required.")
                return
            
            # Prepare payload matching the API expectation
            payload = {
                "user_id": st.session_state.user_id,
                "name": name,
                "category": category,
                "area": area,
                "instructions": instructions,
                "image": image,
                "tags": tags
            }
            
            if make_request(f"{recipe_url}/recipes/", method="POST", data=payload):
                st.success("Recipe saved successfully!")
                st.rerun()
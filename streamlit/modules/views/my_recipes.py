import streamlit as st
from modules.config import RECIPE_CRUD_URL, API_VERSION, RECIPES_FETCH_URL
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
    
    # --- Tags and Ingredients builder (outside the form because buttons aren't allowed inside forms) ---
    # Initialize tag suggestions and ingredient list in session
    if "recipe_tag_suggestions" not in st.session_state:
        # populate tag suggestions with categories from the fetch service (same logic as recipe_search)
        try:
            resp_tags = make_request(f"{RECIPES_FETCH_URL}/categories")
            cats = [c.get("strCategory") for c in (resp_tags.get("categories") if resp_tags else []) if c.get("strCategory")]
        except Exception:
            cats = []
        st.session_state["recipe_tag_suggestions"] = cats
    if "new_recipe_tags_selected" not in st.session_state:
        st.session_state["new_recipe_tags_selected"] = []
    if "new_recipe_ingredients" not in st.session_state:
        st.session_state["new_recipe_ingredients"] = []
    # Clear-input flags: if set, clear the corresponding widget values before widgets are created
    if st.session_state.get("_clear_ui_tag"):
        st.session_state["ui_new_tag"] = ""
        st.session_state.pop("_clear_ui_tag", None)
    if st.session_state.get("_clear_ui_ing"):
        st.session_state["ui_ing_name"] = ""
        st.session_state["ui_ing_measure"] = ""
        st.session_state.pop("_clear_ui_ing", None)

    st.subheader("Add New Recipe")

    # Tags UI
    st.markdown("**Tags**")
    tag_suggestions = st.session_state.get("recipe_tag_suggestions", [])
    if st.button("➕ Add tag", key="ui_add_tag"):
        nt = (st.session_state.get("ui_new_tag") or "").strip()
        if nt:
            if nt not in tag_suggestions:
                tag_suggestions.append(nt)
                st.session_state["recipe_tag_suggestions"] = tag_suggestions
            sel = st.session_state.get("new_recipe_tags_selected", [])
            if nt not in sel:
                sel.append(nt)
                st.session_state["new_recipe_tags_selected"] = sel
            # set flag to clear input on next run (avoid modifying widget state after creation)
            st.session_state["_clear_ui_tag"] = True

    # Ingredients builder
    st.markdown("**Ingredients**")
    ing_c1, ing_c2, ing_c3 = st.columns([4, 2, 1])
    with ing_c1:
        st.text_input("Name", key="ui_ing_name")
    with ing_c2:
        st.text_input("Measure", key="ui_ing_measure")
    with ing_c3:
        if st.button("Add", key="ui_add_ing"):
            n = (st.session_state.get("ui_ing_name") or "").strip()
            m = (st.session_state.get("ui_ing_measure") or "").strip()
            if n:
                lst = st.session_state.get("new_recipe_ingredients")
                lst.append({"name": n, "measure": m})
                st.session_state["new_recipe_ingredients"] = lst
                # set flag to clear inputs on next run
                st.session_state["_clear_ui_ing"] = True

    # Show current ingredients with remove buttons
    if st.session_state.get("new_recipe_ingredients"):
        for idx, ing in enumerate(list(st.session_state.get("new_recipe_ingredients"))):
            r1, r2 = st.columns([5, 1])
            with r1:
                st.write(f"- {ing.get('name')} — {ing.get('measure')}")
            with r2:
                if st.button("Remove", key=f"ui_rm_ing_{idx}"):
                    lst = st.session_state.get("new_recipe_ingredients")
                    lst.pop(idx)
                    st.session_state["new_recipe_ingredients"] = lst

    # Now the main form (no buttons inside)
    with st.form("add_recipe_form"):
        name = st.text_input("Recipe Name *")
        c1, c2 = st.columns(2)
        # Fetch categories from fetch service (TheMealDB) and cache in session
        categories = st.session_state.get("recipe_categories")
        if categories is None:
            try:
                resp = make_request(f"{RECIPES_FETCH_URL}/categories")
                categories = [c.get("strCategory") for c in (resp.get("categories") if resp else []) if c.get("strCategory")]
            except Exception:
                categories = []
            st.session_state["recipe_categories"] = categories

        with c1:
            if categories:
                cat_options = categories + ["Other / Custom"]
                selected_cat = st.selectbox("Category", options=cat_options)
                if selected_cat == "Other / Custom":
                    category = st.text_input("Custom Category")
                else:
                    category = selected_cat
            else:
                category = st.text_input("Category")
            image = st.text_input("Image URL")
        # --- Area (cuisine) selection (fetched) ---
        # Fetch areas from fetch service and cache
        areas = st.session_state.get("recipe_areas")
        if areas is None:
            try:
                resp_a = make_request(f"{RECIPES_FETCH_URL}/areas")
                areas = [a.get("strArea") for a in (resp_a.get("areas") if resp_a else []) if a.get("strArea")]
            except Exception:
                areas = []
            st.session_state["recipe_areas"] = areas

        with c2:
            if areas:
                area_options = areas + ["Other / Custom"]
                selected_area = st.selectbox("Area/Cuisine", options=area_options)
                if selected_area == "Other / Custom":
                    area = st.text_input("Custom Area/Cuisine")
                else:
                    area = selected_area
            else:
                area = st.text_input("Area/Cuisine")

        instructions = st.text_area("Instructions", height=150)

        # (Ingredients UI moved outside form)

        submitted = st.form_submit_button("Save Recipe")
        
        if submitted:
            if not name:
                st.error("Recipe name is required.")
                return
            
            # Collect ingredients from interactive builder (session_state)
            ingredients_list = st.session_state.get("new_recipe_ingredients", [])

            # Resolve tags: merge selected from multiselect (`ui_selected_tags`) and any manually added tags
            multisel = st.session_state.get("ui_selected_tags", []) or []
            added = st.session_state.get("new_recipe_tags_selected", []) or []
            # keep order: multiselect first, then added (avoid duplicates)
            seen = set()
            final_tags = []
            for t in multisel + added:
                if t and t not in seen:
                    final_tags.append(t)
                    seen.add(t)

            # Convert tags to string for DB (comma-separated) to match backend schema
            tags_str = ",".join(final_tags) if final_tags else ""

            # Prepare payload matching the API expectation
            payload = {
                "user_id": st.session_state.user_id,
                "name": name,
                "category": category,
                "area": area,
                "instructions": instructions,
                "ingredients": ingredients_list,
                "image": image,
                "tags": tags_str
            }
            
            if make_request(f"{recipe_url}/recipes/", method="POST", data=payload):
                st.success("Recipe saved successfully!")
                st.rerun()
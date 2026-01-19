import streamlit as st
from modules.config import RECIPES_FETCH_URL, RECIPE_CRUD_URL
from modules.api import make_request
from modules.utils import get_ingredients_list
# Import the new reviews component
from modules.components.reviews import render_reviews_section

def render_recipe_search():
    """Entry point for the Recipe Search feature."""
    st.header("🔍 Recipe Search")
    
    _init_search_state()
    
    # 1. Handle filters & inputs
    # If a search is performed, this returns True and updates session_state
    perform_search = _render_search_filters()
    
    # 2. Reset details cache on new search
    if perform_search:
        st.session_state.loaded_recipes = {} 
    
    # 3. Render the results grid
    _render_search_results()

def _init_search_state():
    """Initialize the required session variables."""
    if "loaded_recipes" not in st.session_state: 
        st.session_state.loaded_recipes = {}
    if "search_results" not in st.session_state: 
        st.session_state.search_results = []

def _render_search_filters():
    """
    Renders search filters and input fields. 
    Returns True if a search was triggered and data was updated.
    """
    st.subheader("Filter Criteria")
    c1, c2 = st.columns([1, 3])
    
    with c1:
        search_type = st.selectbox("Search By", ["Name", "Ingredient", "Category", "Area"])
    
    raw_response = None
    search_triggered = False
    
    with c2:
        if search_type == "Name":
            query = st.text_input("Recipe Name", placeholder="e.g. Lasagna")
            if st.button("Search", key="s_name") and query:
                raw_response = make_request(f"{RECIPES_FETCH_URL}/search/name/{query}")
                search_triggered = True

        elif search_type == "Ingredient":
            query = st.text_input("Ingredient", placeholder="e.g. Garlic")
            if st.button("Search", key="s_ing") and query:
                raw_response = make_request(f"{RECIPES_FETCH_URL}/filter/ingredient/{query}")
                search_triggered = True

        elif search_type == "Category":
            data = make_request(f"{RECIPES_FETCH_URL}/categories") or {}
            opts = [c["strCategory"] for c in data.get("categories", [])]
            sel = st.selectbox("Select Category", opts) if opts else None
            if st.button("Search", key="s_cat") and sel:
                raw_response = make_request(f"{RECIPES_FETCH_URL}/filter/category/{sel}")
                search_triggered = True

        elif search_type == "Area":
            data = make_request(f"{RECIPES_FETCH_URL}/areas") or {}
            raw_list = data.get("areas") or data.get("meals") or []
            opts = [a.get("strArea") for a in raw_list]
            if opts:
                sel = st.selectbox("Select Area", opts)    
                if st.button("Search", key="s_area"):
                    raw_response = make_request(f"{RECIPES_FETCH_URL}/filter/area/{sel}")
                    search_triggered = True
            else:
                st.error("Failed to retrieve the areas.")

    # Process and save results if search occurred
    if search_triggered:
        final_results = []
        if raw_response:
            # Handle TheMealDB format {"meals": [...]}
            if isinstance(raw_response, dict):
                final_results = raw_response.get("meals") or []
            # Handle standard list format
            elif isinstance(raw_response, list):
                final_results = raw_response
        
        # Update the main state variable used by the renderer
        st.session_state.search_results = final_results
        
    return search_triggered

def _render_search_results():
    """Render search results grid supporting both Custom and External recipes."""    
    if "search_results" not in st.session_state:
        st.session_state.search_results = []

    if not st.session_state.search_results:
        return

    seen_ids = set()
    unique_results = []
    
    for meal in st.session_state.search_results:
        internal_id = meal.get("id_recipe") or meal.get("id")
        external_id = meal.get("id_external") or meal.get("id_esterno") or meal.get("idMeal")
        
        if meal.get("is_external"):
            uid = f"ext_{external_id}"
        else:
            uid = f"int_{internal_id}"
            
        if uid not in seen_ids:
            seen_ids.add(uid)
            unique_results.append(meal)
            
    st.success(f"Found {len(unique_results)} recipes (Mixed Custom & External).")
    
    for meal in unique_results:
        is_ext = meal.get("is_external", False)
        name = meal.get("name") or meal.get("strMeal") or "Unknown Recipe"
        
        ext_id = str(meal.get("id_external") or meal.get("id_recipe") or meal.get("idMeal"))
        
        label = f" {name} {' (External)' if is_ext else ' (Custom)'}"
        
        with st.expander(label):
            _render_single_recipe_detail(ext_id, meal, is_external=is_ext)

def _render_single_recipe_detail(item_id, partial_data, is_external=False):
    """
    Render single recipe with Mixed Loading (Internal vs External).
    Supports both custom DB recipes and TheMealDB external recipes.
    """
    
    # 1. SESSION CACHE MANAGEMENT
    # We use a prefix (ext_ or int_) to avoid ID collisions between different data sources
    cache_key = f"{'ext' if is_external else 'int'}_{item_id}"
    cached_data = st.session_state.loaded_recipes.get(cache_key)
    
    # Use cached data if available, otherwise use the partial data from search results
    meal = cached_data if cached_data else partial_data
    
    # Check if we have full details (instructions are the marker for a "full" object)
    # Internal recipes use 'instructions', external use 'strInstructions'
    has_instructions = meal.get("instructions") or meal.get("strInstructions")
    
    # --- LAZY LOADING BLOCK ---
    # If full details are missing, show a button to trigger the specific API call
    if not has_instructions:
        c1, c2 = st.columns([1, 4])
        with c1:
            # Show thumbnail from search results while loading
            thumb = meal.get("image") or meal.get("strMealThumb")
            if thumb:
                st.image(thumb, use_container_width=True)
        with c2:
            st.info(f"Details for {'External' if is_external else 'Custom'} recipe not loaded.")
            
            # API call happens ONLY when this specific button is clicked
            if st.button("📥 Load Details & Reviews", key=f"load_{cache_key}"):
                with st.spinner("Fetching data..."):
                    # ROUTING LOGIC:
                    # External recipes -> recipes-fetch-service
                    # Custom recipes -> recipe-crud-interaction (orchestrator)
                    if is_external:
                        url = f"{RECIPES_FETCH_URL}/recipe/{item_id}"
                    else:
                        url = f"{RECIPE_CRUD_URL}/api/v1/recipes/{item_id}"
                    
                    full = make_request(url)
                    
                    if full:
                        # Normalize response (TheMealDB wraps results in a 'meals' list)
                        final_meal = full["meals"][0] if "meals" in full else full
                        
                        # Store in session cache to avoid re-fetching
                        st.session_state.loaded_recipes[cache_key] = final_meal
                        st.rerun() # Refresh UI to show full details
        return

    # --- FULL DETAILS RENDERING ---
    # 2. VARIABLE NORMALIZATION
    # Aligning field names from different sources (DB vs External API)
    name = meal.get("name") or meal.get("strMeal")
    category = meal.get("category") or meal.get("strCategory")
    area = meal.get("area") or meal.get("strArea")
    thumb = meal.get("image") or meal.get("strMealThumb")
    
    # Format instructions for better readability in Streamlit
    raw_instructions = meal.get("instructions") or meal.get("strInstructions") or "No instructions available."
    instructions = raw_instructions.replace("\r\n", "\n\n").replace("\n", "\n\n")

    # 3. VISUAL LAYOUT
    c_img, c_desc = st.columns([1, 2])
    with c_img:
        if thumb:
            st.image(thumb, use_container_width=True) 
        
        st.markdown("**Ingredients:**")
        # get_ingredients_list is already designed to handle both list and strIngredientX formats
        for line in get_ingredients_list(meal):
            st.markdown(f"<small>{line}</small>", unsafe_allow_html=True)
            
    with c_desc:
        st.subheader(name)
        st.caption(f"Category: {category} | Area: {area} | Source: {'🌐 External' if is_external else '🏠 Community'}")
        st.write(instructions)

    # 4. REVIEW COMPONENT
    st.divider()
    
    # For external recipes, the review system will handle "Shadow Import" automatically
    if is_external:
        render_reviews_section(external_id=item_id, recipe_name=name)
    else:
        # For internal recipes, we pass the direct primary key from our DB
        render_reviews_section(recipe_id=int(item_id), recipe_name=name)
import streamlit as st
from modules.config import RECIPES_FETCH_URL
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
    """Render search results grid with robust deduplication."""
    
    # 1. Safe initialization
    if "search_results" not in st.session_state:
        st.session_state.search_results = []

    # 2. Exit silently if no results
    if not st.session_state.search_results:
        return

    # 3. ROBUST DEDUPLICATION (Fixes Duplicate Key Error)
    seen_ids = set()
    unique_results = []
    
    for meal in st.session_state.search_results:
        # Get ID from either format
        mid = meal.get("id") or meal.get("idMeal")
        
        if mid:
            # FORCE STRING CONVERSION!
            # This ensures that 53284 (int) and "53284" (str) are treated as the same ID
            mid_str = str(mid)
            
            if mid_str not in seen_ids:
                seen_ids.add(mid_str)
                unique_results.append(meal)
            
    # 4. Rendering
    st.success(f"Found {len(unique_results)} recipes.")
    
    for meal in unique_results:
        # Secure ID for widget keys (Always use the string version)
        raw_id = meal.get("id") or meal.get("idMeal")
        ext_id = str(raw_id) 
        
        # Secure Name for display
        name = meal.get("name") or meal.get("strMeal") or "Unknown Recipe"
        
        # Expandable Box
        with st.expander(f"{name}"):
            _render_single_recipe_detail(ext_id, meal)

def _render_single_recipe_detail(ext_id, partial_data):
    """
    Render single recipe with TRUE Lazy Loading.
    Fetches data only when the user explicitly asks for it.
    """
    
    # 1. Check if data is already in session cache
    cached_data = st.session_state.loaded_recipes.get(ext_id)
    
    # Use cached data if available, otherwise use the partial data from search results
    meal = cached_data if cached_data else partial_data
    
    # Check if we have full details (e.g., instructions)
    has_instructions = meal.get("strInstructions") or meal.get("instructions")
    
    # --- LAZY LOADING BLOCK ---
    # If we DO NOT have instructions, we only show a "Load" button.
    # No API calls happen here unless the button is clicked.
    if not has_instructions:
        c1, c2 = st.columns([1, 4])
        with c1:
             # Display the thumbnail we already have from the search list
             thumb = meal.get("image") or meal.get("strMealThumb")
             if thumb:
                 st.image(thumb, width="stretch")
        with c2:
            st.info("Details not loaded yet.")
            
            # THE KEY: The make_request call happens ONLY if this specific button is clicked
            if st.button("📥 Load Recipe & Reviews", key=f"load_{ext_id}"):
                with st.spinner("Downloading data..."):
                    full = make_request(f"{RECIPES_FETCH_URL}/recipe/{ext_id}")
                    
                    if full:
                        # Handle different API response structures (list vs dict)
                        if "meals" in full:
                            final_meal = full["meals"][0]
                        else:
                            final_meal = full
                        
                        # Save to session_state so we skip this block on the next refresh
                        st.session_state.loaded_recipes[ext_id] = final_meal
                        st.rerun() # Reload the script to render the full view immediately
                        
        return # STOP! Stop execution here to prevent rendering missing data.

    # --- FULL DETAILS RENDERING ---
    # If code reaches here, data is loaded and cached.
    
    # 2. Normalize Variables (Backend vs TheMealDB)
    name = meal.get("name") or meal.get("strMeal")
    category = meal.get("category") or meal.get("strCategory")
    area = meal.get("area") or meal.get("strArea")
    thumb = meal.get("image") or meal.get("strMealThumb")
    
    raw_instructions = meal.get("instructions") or meal.get("strInstructions") or "No instructions available."
    # Fix formatting for readability
    instructions = raw_instructions.replace("\r\n", "\n\n").replace("\n", "\n\n")

    # 3. Visual Layout 
    c_img, c_desc = st.columns([1, 2])
    with c_img:
        if thumb:
            st.image(thumb, width="stretch") 
        
        st.markdown("**Ingredients:**")
        for line in get_ingredients_list(meal):
            st.markdown(f"<small>{line}</small>", unsafe_allow_html=True)
            
    with c_desc:
        st.subheader(name)
        st.caption(f"Category: {category} | Area: {area}")
        st.write(instructions)

    # 4. Review Component (Loaded only after the recipe details are confirmed)
    st.divider()
    render_reviews_section(external_id=ext_id, recipe_name=name)
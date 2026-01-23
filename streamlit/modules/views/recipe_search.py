import streamlit as st
import urllib.parse
from modules.config import RECIPES_FETCH_URL, RECIPE_CRUD_URL, API_VERSION
from modules.api import make_request
from modules.utils import get_ingredients_list
from modules.components.reviews import render_reviews_section

recipe_crud_url = f"{RECIPE_CRUD_URL}/{API_VERSION}"

def render_recipe_search():
    """Entry point for the Recipe Search feature."""
    st.header("🔍 Recipe Search")
    
    _init_search_state()
    
    # 1. Handle filters & inputs
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
    Renders search filters. 
    """
    st.subheader("Filter Criteria")
    c1, c2 = st.columns([1, 3])
    
    with c1:
        search_type = st.selectbox("Search By", ["Name", "Ingredient", "Category", "Area"])
    
    raw_response = None
    search_triggered = False
    
    base_search_url = f"{recipe_crud_url}/recipes/search"

    with c2:
        def execute_search(params_key, value):
            if value:
                safe_val = urllib.parse.quote_plus(value)
                return make_request(f"{base_search_url}?{params_key}={safe_val}")
            return None

        # --- SEARCH BY NAME ---
        if search_type == "Name":
            query = st.text_input("Recipe Name", placeholder="e.g. Lasagna")
            if st.button("Search", key="s_name"):
                raw_response = execute_search("q", query)
                search_triggered = True

        # --- SEARCH BY INGREDIENT ---
        elif search_type == "Ingredient":
            query = st.text_input("Ingredient", placeholder="e.g. Garlic")
            if st.button("Search", key="s_ing"):
                raw_response = execute_search("ingredient", query)
                search_triggered = True

        # --- SEARCH BY CATEGORY ---
        elif search_type == "Category":
            cat_data = make_request(f"{RECIPES_FETCH_URL}/categories")
            opts = [c["strCategory"] for c in cat_data.get("categories", [])] if cat_data else []
            
            sel = st.selectbox("Select Category", opts) if opts else None
            if st.button("Search", key="s_cat") and sel:
                raw_response = execute_search("category", sel)
                search_triggered = True

        # --- SEARCH BY AREA ---
        elif search_type == "Area":
            area_data = make_request(f"{RECIPES_FETCH_URL}/areas")
            raw_list = []
            if area_data:
                raw_list = area_data.get("areas") or area_data.get("meals") or []
            
            opts = [a.get("strArea") for a in raw_list]
            
            if opts:
                sel = st.selectbox("Select Area", opts)    
                if st.button("Search", key="s_area"):
                    raw_response = execute_search("area", sel)
                    search_triggered = True
            else:
                st.warning("Could not load areas list.")

    # Process results
    if search_triggered:
        final_results = []
        if raw_response:
            if isinstance(raw_response, list):
                final_results = raw_response
            elif isinstance(raw_response, dict) and "meals" in raw_response:
                final_results = raw_response.get("meals") or []
        
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
        internal_id = meal.get("id") 
        external_id = meal.get("external_id")
        
        is_ext = meal.get("source") == "external" or (meal.get("is_custom") is False)
        
        if is_ext:
            uid = f"ext_{external_id}"
        else:
            uid = f"int_{internal_id}"
            
        if uid not in seen_ids:
            seen_ids.add(uid)
            meal["is_external_flag"] = is_ext
            unique_results.append(meal)
            
    st.success(f"Found {len(unique_results)} recipes (Mixed Custom & External).")
    
    for meal in unique_results:
        is_ext = meal.get("is_external_flag", False)
        name = meal.get("name") or "Unknown Recipe"
        
        pass_id = meal.get("external_id") if is_ext else meal.get("id")
        
        source_label = "🌐 External" if is_ext else "🏠 Custom"
        label = f"{name} ({source_label})"
        
        with st.expander(label):
            _render_single_recipe_detail(str(pass_id), meal, is_external=is_ext)

def _render_single_recipe_detail(item_id, partial_data, is_external=False):
    
    # 1. SESSION CACHE MANAGEMENT
    cache_key = f"{'ext' if is_external else 'int'}_{item_id}"
    cached_data = st.session_state.loaded_recipes.get(cache_key)
    
    meal = cached_data if cached_data else partial_data
    
    name = meal.get("name") or meal.get("strMeal") or "Unknown Recipe"

    # Check if full details are loaded
    has_instructions = meal.get("instructions") or meal.get("strInstructions")
    
    if not has_instructions:
        c1, c2 = st.columns([1, 4])
        with c1:
            thumb = meal.get("image") or meal.get("strMealThumb")
            if thumb:
                st.image(thumb, width="stretch")
        with c2:
            st.info(f"Summary view for {name}. Click below for details.")
            
            if st.button("📥 Load Full Details", key=f"load_{cache_key}"):
                with st.spinner("Fetching data..."):
                    url = f"{recipe_crud_url}/recipes/{item_id}"
                    
                    full = make_request(url)
                    
                    if full:
                        final_meal = full[0] if isinstance(full, list) and full else full
                        if isinstance(full, dict) and "meals" in full:
                             final_meal = full["meals"][0]

                        st.session_state.loaded_recipes[cache_key] = final_meal
                        st.rerun()
        return

    # --- RENDERING ---
    category = meal.get("category") or meal.get("strCategory")
    area = meal.get("area") or meal.get("strArea")
    thumb = meal.get("image") or meal.get("strMealThumb")
    
    raw_instructions = meal.get("instructions") or meal.get("strInstructions") or "No instructions."
    instructions = raw_instructions.replace("\r\n", "\n\n").replace("\n", "\n\n")

    c_img, c_desc = st.columns([1, 2])
    with c_img:
        if thumb: st.image(thumb, width="stretch")
        
        st.markdown("#### Ingredients")
        for line in get_ingredients_list(meal):
            st.caption(f"• {line}")
            
    with c_desc:
        st.subheader(name)
        st.caption(f"Category: {category} | Area: {area}")
        st.write(instructions)

    st.divider()
    
    if is_external:
        rec_id_val = None
        ext_id_val = str(item_id)
    else:
        rec_id_val = int(item_id)
        ext_id_val = meal.get("external_id")

    render_reviews_section(
        recipe_id=rec_id_val, 
        external_id=ext_id_val, 
        recipe_name=name
    )

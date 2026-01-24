import streamlit as st
from modules.config import RECIPE_CRUD_URL, API_VERSION
from modules.api import make_request

recipe_url = f"{RECIPE_CRUD_URL}/{API_VERSION}"

def render_reviews_section(external_id, recipe_name, recipe_id=None):
    """
    Component used in recipe detail views.
    Handles both External (MealDB) and Internal (Custom) recipes safely.
    """
    safe_ext_id = str(external_id)

    st.markdown("---")
    st.subheader(f"Reviews for {recipe_name}")

    _render_reviews_list(safe_ext_id, recipe_id)
    _render_review_form(safe_ext_id, recipe_id)

def _render_reviews_list(external_id, recipe_id):
    # 1. FETCH (Internal vs External)
    is_custom_pure = (external_id == "None" or not external_id) and recipe_id
    
    if is_custom_pure:
        fetch_url = f"{recipe_url}/reviews/recipe/{recipe_id}?type=internal"
    else:
        if external_id == "None":
            st.warning("Cannot load reviews: Missing recipe ID.")
            return
        fetch_url = f"{recipe_url}/reviews/recipe/{external_id}?type=external"

    # 2. API CALL
    reviews = make_request(fetch_url)
    
    if not reviews:
        st.info("No reviews yet. Be the first to review!")
        return

    # 3. RENDER LIST
    for rev in reviews:
        with st.container(border=True):
            c1, c2 = st.columns([6, 1])
            with c1:
                rating_val = rev.get('rating', 0)
                stars = "★" * rating_val + "☆" * (5 - rating_val)
                st.markdown(f"**{rev.get('username', 'Unknown')}** {stars}")
                st.write(rev.get('comment', ''))
                st.caption(f"Date: {rev.get('created_at', '')[:10]}")
            
            with c2:
                current_user_id = st.session_state.get("user_id")
                if current_user_id and str(rev.get("user_id")) == str(current_user_id):
                    btn_key = f"del_{external_id}_{rev['id']}"
                    
                    if st.button("🗑️", key=btn_key, help="Delete your review"):
                        if make_request(f"{recipe_url}/reviews/{rev['id']}", method="DELETE"):
                            st.toast("Review deleted!")
                            st.rerun()

def _render_review_form(external_id, recipe_id):
    st.markdown("#### Write a Review")
    
    if recipe_id:
        unique_suffix = f"int_{recipe_id}"
    else:
        unique_suffix = f"ext_{external_id}"

    form_key = f"form_review_{unique_suffix}"
    
    with st.form(key=form_key):
        col1, col2 = st.columns([1, 4])
        with col1:
            rating = st.slider("Rating", 1, 5, 5)
        with col2:
            comment = st.text_area("Comment", height=70, placeholder="Share your experience...")
        
        submitted = st.form_submit_button("Submit Review")
        
        if submitted:
            if not st.session_state.get("user_id"):
                st.error("You must be logged in to post a review.")
                return

            if not comment:
                st.warning("Please write a comment.")
                return

            payload = {
                "rating": rating, 
                "comment": comment, 
                "external_id": external_id if external_id != "None" else None,
                "recipe_id": recipe_id
            }
            
            if make_request(f"{recipe_url}/reviews/", method="POST", data=payload):
                st.success("Review posted!")
                st.rerun()
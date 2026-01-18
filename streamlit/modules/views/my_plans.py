import streamlit as st
from modules.config import MEAL_PLANNER_URL
from modules.api import make_request

def render_my_meal_plans():
    """
    Displays the history of saved meal plans for the current user.
    """
    st.header("📋 My Meal Plans History")
    
    user_id = st.session_state.get("user_id")
    if not user_id:
        st.warning("Please login to view your plans.")
        return

    # Fetch list of plans
    result = make_request(f"{MEAL_PLANNER_URL}/meal-plans/user/{user_id}")
    
    if result and result.get("meal_plans"):
        plans = result["meal_plans"]
        
        for plan in plans:
            label = f"Plan from {plan['start_date']} to {plan['end_date']}"
            with st.expander(label):
                st.caption(f"Created at: {plan.get('created_at')} | ID: {plan['id']}")
                
                # Fetch summary of items for preview (optional)
                items_data = make_request(f"{MEAL_PLANNER_URL}/meal-plans/{plan['id']}/items")
                if items_data and items_data.get("items"):
                    st.write(f"Contains **{len(items_data['items'])}** meals.")
                
                # Action Buttons
                c1, c2 = st.columns([1, 4])
                with c1:
                    # LOAD Action
                    if st.button("📂 Load Plan", key=f"load_p_{plan['id']}", type="primary"):
                        full_plan = make_request(f"{MEAL_PLANNER_URL}/meal-plans/{plan['id']}/full")
                        if full_plan:
                            st.session_state.current_meal_plan = full_plan
                            st.success("Plan loaded into 'Meal Planning' tab!")
                            # Optional: Redirect logic could go here if Streamlit supported simple redirects
                with c2:
                    # DELETE Action
                    if st.button("🗑️ Delete", key=f"del_p_{plan['id']}", type="secondary"):
                        if make_request(f"{MEAL_PLANNER_URL}/meal-plans/{plan['id']}", method="DELETE"):
                            st.toast("Plan deleted.")
                            st.rerun()
    else:
        st.info("No saved meal plans found.")
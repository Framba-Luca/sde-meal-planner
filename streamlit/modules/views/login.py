import streamlit as st
import requests
from modules.config import AUTH_SERVICE_URL
from modules.api import make_request
from modules.auth import fetch_current_user, cookie_manager

def render_login_page():
    st.title("🍽️ Meal Planner")
    
    tab1, tab2, tab3 = st.tabs(["Login", "Register", "Google OAuth"])
    
    # --- TAB Classic Logic ---
    with tab1:
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        
        if st.button("Login"):
            if username and password:
                data = {"username": username, "password": password}
                # Classic Login
                result = make_request(f"{AUTH_SERVICE_URL}/api/v1/auth/login", method="POST", data=data, use_form_data=True)
                
                if result and "access_token" in result:
                    # 1. Save token in session
                    st.session_state.token = result["access_token"]
                    
                    # 2. Retrieve user data 
                    if fetch_current_user():
                        st.success("Login successful!")
                        cookie_manager.set("access_token", result["access_token"], key="login_token")
                        st.rerun()
                    else:
                        st.error("Login failed: Token valid but unable to fetch user profile.")
            else:
                st.warning("Enter username and password")
    
    with tab2:
        render_register_tab()
    
    with tab3:
        render_google_tab()

def render_register_tab():
    st.subheader("Create Account")
    reg_u = st.text_input("Username", key="reg_u")
    reg_p = st.text_input("Password", type="password", key="reg_p")
    reg_fn = st.text_input("Full Name", key="reg_fn")
    reg_e = st.text_input("Email", key="reg_e")
    
    if st.button("Register"):
        data = {"username": reg_u, "password": reg_p, "full_name": reg_fn, "email": reg_e}
        
        if make_request(f"{AUTH_SERVICE_URL}/api/v1/auth/register", method="POST", data=data):
            st.success("Account created! Please login.")

def render_google_tab():
    st.subheader("Google Login")
    if st.button("Login with Google"):
        try:
            # Richiediamo l'URL di redirect al backend
            resp = requests.get(f"{AUTH_SERVICE_URL}/api/v1/auth/google/login", allow_redirects=False)
            if resp.status_code == 307:
                st.link_button("Continue to Google", resp.headers.get("location"), type="primary")
            else:
                st.error("Auth Error: Could not get Google URL")
        except Exception as e:
            st.error(f"Connection Error: {e}")
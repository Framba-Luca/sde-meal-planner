import streamlit as st
import extra_streamlit_components as stx
from modules.config import AUTH_SERVICE_URL
from modules.api import make_request
import time

# --- 1. Cookie Management ---
def get_cookie_manager():
    return stx.CookieManager()

cookie_manager = get_cookie_manager()

# --- 2. Logout Function ---
def logout():
    """
    Performs a complete logout.
    """
    cookie_manager.delete("access_token")
    
    keys_to_clear = ["authenticated", "user", "user_id", "token", "current_meal_plan"]
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
            
    st.session_state.authenticated = False
    st.session_state.token = None
    st.rerun()

# --- 3. User Data Fetching ---
def fetch_current_user():
    token = st.session_state.get("token")
    if not token: return False
    
    # /me ora restituisce subito l'ID!
    user_data = make_request(f"{AUTH_SERVICE_URL}/api/v1/auth/me")
    
    if user_data and "id" in user_data:
        st.session_state.user = user_data
        st.session_state.user_id = user_data["id"]
        st.session_state.authenticated = True
        return True
    return False

# --- 4. Session Initialization ---
def initialize_session_state():
    """
    Handles session lifecycle.
    """
    # Init default variables
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "token" not in st.session_state:
        st.session_state.token = None

    # --- FIX 1: Priorità alla Sessione già attiva ---
    # Se siamo già autenticati (es. dopo il primo passaggio del login),
    # controlliamo solo se dobbiamo pulire l'URL.
    if st.session_state.authenticated:
        if "access_token" in st.query_params:
            st.query_params.clear()
            # Non facciamo rerun qui per evitare loop, lasciamo che l'app continui
        return

    # --- FIX 2: Gestione Cookie ---
    cookie_token = cookie_manager.get(cookie="access_token")
    if cookie_token and not st.session_state.authenticated:
        st.session_state.token = cookie_token
        if not fetch_current_user():
            # Cookie invalido/scaduto
            cookie_manager.delete("access_token")
            st.session_state.token = None
        else:
            # Login via cookie riuscito -> return immediato
            return

    # --- FIX 3: Gestione Google OAuth (Parametri URL) ---
    query_params = st.query_params
    if "access_token" in query_params:
        token = query_params["access_token"]
        
        # Impostiamo il token
        st.session_state.token = token
        
        if fetch_current_user():
            # SUCCESS:
            # 1. Impostiamo il cookie
            cookie_manager.set("access_token", token, key="google_auth_token")
            # 2. Puliamo l'URL
            st.query_params.clear()
            # 3. Importante: Rerun per aggiornare la UI e rimuovere i parametri visivamente
            st.rerun()
        else:
            # FAIL: Token invalido
            st.error("Login failed: The token received is invalid or expired.")
            # Puliamo tutto per evitare loop infiniti
            st.session_state.token = None
            st.query_params.clear()
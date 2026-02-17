import streamlit as st
import extra_streamlit_components as stx
from modules.config import AUTH_SERVICE_URL
from modules.api import make_request

# --- 1. Cookie Management ---
def get_cookie_manager():
    return stx.CookieManager()

cookie_manager = get_cookie_manager()

# --- 2. Logout Function ---
def logout():
    """
    Performs a complete logout.
    """
    # Delete cookies safely (handle case where they don't exist)
    try:
        cookie_manager.delete("access_token", key="delete_access_token")
    except KeyError:
        pass
    
    try:
        cookie_manager.delete("refresh_token", key="delete_refresh_token")
    except KeyError:
        pass
    
    keys_to_clear = ["authenticated", "user", "user_id", "token", "refresh_token", "current_meal_plan"]
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
            
    st.session_state.authenticated = False
    st.session_state.token = None
    st.session_state.refresh_token = None

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
    if "refresh_token" not in st.session_state:
        st.session_state.refresh_token = None

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
    cookie_refresh = cookie_manager.get(cookie="refresh_token")
    if cookie_token and not st.session_state.authenticated:
        st.session_state.token = cookie_token
        st.session_state.refresh_token = cookie_refresh
        if not fetch_current_user():
            # Cookie invalido/scaduto
            cookie_manager.delete("access_token")
            cookie_manager.delete("refresh_token")
            st.session_state.token = None
            st.session_state.refresh_token = None
        else:
            # Login via cookie riuscito -> return immediato
            return

    # --- FIX 3: Gestione Google OAuth (Parametri URL) ---
    query_params = st.query_params
    if "access_token" in query_params:
        token = query_params["access_token"]
        refresh_token = query_params.get("refresh_token")
        
        # Impostiamo i token
        st.session_state.token = token
        st.session_state.refresh_token = refresh_token
        
        if fetch_current_user():
            # SUCCESS:
            # 1. Impostiamo i cookie
            cookie_manager.set("access_token", token, key="google_auth_token")
            if refresh_token:
                cookie_manager.set("refresh_token", refresh_token, key="google_refresh_token")
            # 2. Puliamo l'URL
            st.query_params.clear()
            # 3. Importante: Rerun per aggiornare la UI e rimuovere i parametri visivamente
            st.rerun()
        else:
            # FAIL: Token invalido
            st.error("Login failed: The token received is invalid or expired.")
            # Puliamo tutto per evitare loop infiniti
            st.session_state.token = None
            st.session_state.refresh_token = None
            st.query_params.clear()
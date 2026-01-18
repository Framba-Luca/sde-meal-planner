import streamlit as st
import requests

def make_request(url, method="GET", data=None, use_form_data=False):
    """
    Make HTTP request to a service with automatic token handling.
    """
    headers = {}

    # Check if a token exists in session_state, regardless of 'authenticated' flag.
    # This allows calling /me during the login handshake.
    token = st.session_state.get("token")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    # Validation for form data
    assert not use_form_data or method == "POST", "use_form_data is only valid for POST requests"

    try:
        response = None
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            if use_form_data:
                response = requests.post(url, data=data, headers=headers)
            else:
                response = requests.post(url, json=data, headers=headers)
        elif method == "PUT":
            response = requests.put(url, json=data, headers=headers)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers)
        
        if response is None:
            return None
            
        # Response handling
        if response.status_code in [200, 201]:
            return response.json()
            
        elif response.status_code == 401:
            # Handle unauthorized access
            # Only trigger a full logout/rerun if we thought we were authenticated
            if st.session_state.get("authenticated"):
                st.error("Session expired. Please login again.")
                st.session_state.authenticated = False
                st.session_state.token = None
                st.rerun()
            return None
            
        elif response.status_code == 403:
            st.error("Access denied.")
            
        elif response.status_code == 422:
            try:
                detail = response.json().get('detail')
                st.error(f"Validation Error (422): {detail}")
            except:
                st.error(f"Validation Error (422): {response.text}")
            
        return None
        
    except requests.RequestException as e:
        st.error(f"Error connecting to service: {e}")
        return None
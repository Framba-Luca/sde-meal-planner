import requests
from fastapi import HTTPException, status
from src.core.config import settings

class AuthClient:

    def __init__(self):
        pass

    def get_user_id_from_token(self, token: str) -> int:
        """
        Calls GET /api/v1/users/me on Auth Service to validate the toke.
        """
        url = f"{settings.AUTHENTICATION_SERVICE_URL}{settings.API_V1_STR}/users/me"
        
        headers = {
            "Authorization": f"Bearer {token}"
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=5)
            
            if response.status_code == 200:
                user_data = response.json()
                return user_data["id"]
            
            elif response.status_code == 401:
                raise HTTPException(status_code=401, detail="Invalid Token")
            else:
                raise HTTPException(status_code=401, detail="Failed Authentication")
                
        except requests.RequestException:
            raise HTTPException(
                status_code=503, 
                detail="Authentication Service not available"
            )
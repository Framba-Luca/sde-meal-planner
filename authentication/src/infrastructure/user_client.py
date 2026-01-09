import httpx
from typing import Optional, Dict, Any
from src.core.config import settings
from src.schemas.user import UserCreate
import src.core.exceptions as exc 

class UserRemoteRepository:
    def __init__(self):
        self.base_url = settings.DATABASE_SERVICE_URL
        # Timeout aggressivo: se il DB non risponde in 5 secondi, è inutile aspettare
        self.timeout = httpx.Timeout(5.0, connect=2.0)

    async def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(f"{self.base_url}/users/username/{username}")
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 404:
                    return None
                else:
                    # Se il DB service risponde 500, per noi è "ServiceUnavailable"
                    raise exc.ServiceUnavailable(f"Database Service error: {response.status_code}")
                    
            except httpx.RequestError as e:
                # Qui catturiamo timeout, connessione rifiutata, dns error...
                print(f"Connection error to Database Service: {e}")
                raise exc.ServiceUnavailable("Database service is unreachable")

    async def create_user(self, user_in: UserCreate, hashed_password: str) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            payload = {
                "username": user_in.username,
                "full_name": user_in.full_name,
                "hashed_password": hashed_password,
                "disabled": False
            }
            
            try:
                response = await client.post(f"{self.base_url}/users", json=payload)
                
                if response.status_code in (200, 201):
                    return response.json()
                elif response.status_code == 400:
                    # Assumiamo che 400 dal DB significhi "Utente già esiste" o dati invalidi
                    raise exc.UserAlreadyExists("User might already exist")
                else:
                    raise exc.ServiceUnavailable(f"Database Service failed with {response.status_code}")
                    
            except httpx.RequestError:
                raise exc.ServiceUnavailable("Database service is unreachable during creation")
            
    async def get_users(self, skip: int = 0, limit: int = 100) -> list:
        """Retrieves the user list from DB Service"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                # Assume the db-service has a GET /users route
                response = await client.get(
                    f"{self.base_url}/users",
                    params={"skip": skip, "limit": limit}
                )
                if response.status_code == 200:
                    return response.json()
                return []
            except httpx.RequestError:
                # If the DB is not responding, return empty list or raise exception
                # For a list, better return empty than break everything
                return []
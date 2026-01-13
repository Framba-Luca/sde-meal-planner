import httpx
import secrets
from urllib.parse import urlencode
from src.core.config import settings
from src.core import security
from src.core import exceptions as exc
from src.schemas.token import Token
from src.schemas.user import UserCreate, User
from src.infrastructure.user_client import UserRemoteRepository

class GoogleAuthService:
    def __init__(self, user_repo: UserRemoteRepository):
        self.user_repo = user_repo

    def get_login_url(self) -> str:
        """Create the URL for redirecting to Google login page."""
        params = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "response_type": "code",
            "scope": "openid email profile",
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "access_type": "offline",
            "prompt": "consent"
        }
        return f"https://accounts.google.com/o/oauth2/auth?{urlencode(params)}"
    
    async def callback_handler(self, code: str) -> Token:
        """
        Exchange the 'code' received from Google with the JWT Token of platform.
        """
        async with httpx.AsyncClient() as client:
            # 1. Exchange code for access token
            token_url = "https://oauth2.googleapis.com/token"
            data = {
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            }
            
            token_resp = await client.post(token_url, data=data)
            if token_resp.status_code != 200:
                raise exc.InvalidCredentials("Failed to retrieve token from Google")
            
            google_access_token = token_resp.json().get("access_token")

            # 2. Uses the Google Token to retrieve user data
            user_info_resp = await client.get(
                "https://www.googleapis.com/oauth2/v1/userinfo",
                headers={"Authorization": f"Bearer {google_access_token}"}
            )
            google_user_data = user_info_resp.json()

        # 3. Extract necessary user data
        email = google_user_data.get("email")
        if not email:
            raise exc.InvalidCredentials("Google account has no email")
            
        username = email.split("@")[0] # Use as username the part before @
        full_name = google_user_data.get("name", username)

        # 4. Checks if user exists in our DB
        # Sappiamo che questo ritorna un DIZIONARIO o None
        db_user = await self.user_repo.get_user_by_username(username)

        if not db_user:
            # 5. JIT Provisioning: Create the user in our DB
            random_password = secrets.token_urlsafe(32)
            
            # NOTA: Ho aggiunto la virgola che mancava dopo full_name
            user_in = UserCreate(
                username=username,
                password=random_password,
                full_name=full_name, 
                email=email
            )
            
            hashed_pw = security.get_password_hash(random_password)
            # Sappiamo che questo ritorna un DIZIONARIO
            db_user = await self.user_repo.create_user(user_in, hashed_pw)
            
            if not db_user:
                raise exc.ServiceUnavailable("Could not create Google user locally")

        # --- PREPARAZIONE DATI (PULIZIA) ---
        # Creiamo una copia per non modificare l'originale
        user_data_clean = db_user.copy()
        
        # Rimuoviamo la password hashata se presente, altrimenti Pydantic potrebbe lamentarsi
        # quando creeremo User(**user_data_clean)
        if "hashed_password" in user_data_clean:
            del user_data_clean["hashed_password"]

        uid = db_user["username"]
        fullname_claim = db_user.get("full_name")

        # 6. Create the platform JWT Token
        access_token = security.create_access_token(
            subject=uid,
            extra_claims={"full_name": fullname_claim}
        )

        refresh_token = security.create_refresh_token(subject=uid)

        # 7. Return Token
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            # Spacchettiamo il dizionario pulito (senza password) per riempire il modello User
            user=User(**user_data_clean)
        )

        """
        Exchange the 'code' received from Google with the JWT Token of platform.
        """
        async with httpx.AsyncClient() as client:
            # 1. Exchange code for access token
            token_url = "https://oauth2.googleapis.com/token"
            data = {
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            }
            
            token_resp = await client.post(token_url, data=data)
            if token_resp.status_code != 200:
                raise exc.InvalidCredentials("Failed to retrieve token from Google")
            
            google_access_token = token_resp.json().get("access_token")

            # 2. Uses the Google Token to retrieve user data
            user_info_resp = await client.get(
                "https://www.googleapis.com/oauth2/v1/userinfo",
                headers={"Authorization": f"Bearer {google_access_token}"}
            )
            google_user_data = user_info_resp.json()

        # 3. Extract necessary user data
        email = google_user_data.get("email")
        if not email:
            raise exc.InvalidCredentials("Google account has no email")
            
        username = email.split("@")[0] # Use as username the part before @
        full_name = google_user_data.get("name", username)

        # 4. Checks if user exists in our DB
        # Sappiamo che questo ritorna un DIZIONARIO o None
        db_user = await self.user_repo.get_user_by_username(username)

        if not db_user:
            # 5. JIT Provisioning: Create the user in our DB
            random_password = secrets.token_urlsafe(32)
            
            # NOTA: Ho aggiunto la virgola che mancava dopo full_name
            user_in = UserCreate(
                username=username,
                password=random_password,
                full_name=full_name, 
                email=email
            )
            
            hashed_pw = security.get_password_hash(random_password)
            # Sappiamo che questo ritorna un DIZIONARIO
            db_user = await self.user_repo.create_user(user_in, hashed_pw)
            
            if not db_user:
                raise exc.ServiceUnavailable("Could not create Google user locally")

        # --- PREPARAZIONE DATI (PULIZIA) ---
        # Creiamo una copia per non modificare l'originale
        user_data_clean = db_user.copy()
        
        # Rimuoviamo la password hashata se presente, altrimenti Pydantic potrebbe lamentarsi
        # quando creeremo User(**user_data_clean)
        if "hashed_password" in user_data_clean:
            del user_data_clean["hashed_password"]

        uid = db_user["username"]
        fullname_claim = db_user.get("full_name")

        # 6. Create the platform JWT Token
        access_token = security.create_access_token(
            subject=uid,
            extra_claims={"full_name": fullname_claim}
        )

        refresh_token = security.create_refresh_token(subject=uid)

        # 7. Return Token
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            # Spacchettiamo il dizionario pulito (senza password) per riempire il modello User
            user=User(**user_data_clean)
        )
"""
Authentication Service - Handles user authentication with OAuth2 and JWT
"""
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import os
import requests
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi import HTTPException, status

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# Google OAuth2 Configuration
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8001/auth/google/callback")

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """Service for handling authentication operations"""
    
    def __init__(self):
        # In-memory user database (in production, use a real database)
        self.users_db: Dict[str, Dict[str, Any]] = {}
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Hash a password"""
        return pwd_context.hash(password)
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode a JWT token"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except JWTError:
            return None
    
    def get_user(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user by username"""
        return self.users_db.get(username)
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate a user with username and password"""
        user = self.get_user(username)
        if not user:
            return None
        if not self.verify_password(password, user["hashed_password"]):
            return None
        return user
    
    def create_user(self, username: str, password: str, full_name: Optional[str] = None) -> Dict[str, Any]:
        """Create a new user"""
        if username in self.users_db:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
        
        user = {
            "username": username,
            "full_name": full_name or username,
            "hashed_password": self.get_password_hash(password),
            "disabled": False,
            "created_at": datetime.utcnow().isoformat()
        }
        self.users_db[username] = user
        return user
    
    def get_google_auth_url(self) -> str:
        """Get Google OAuth2 authorization URL"""
        auth_url = (
            f"https://accounts.google.com/o/oauth2/v2/auth?"
            f"client_id={GOOGLE_CLIENT_ID}&"
            f"redirect_uri={GOOGLE_REDIRECT_URI}&"
            f"response_type=code&"
            f"scope=openid email profile"
        )
        return auth_url
    
    def exchange_code_for_token(self, code: str) -> Optional[Dict[str, Any]]:
        """Exchange authorization code for access token"""
        token_url = "https://oauth2.googleapis.com/token"
        data = {
            "code": code,
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri": GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code"
        }
        
        try:
            response = requests.post(token_url, data=data)
            response.raise_for_status()
            return response.json()
        except requests.RequestException:
            return None
    
    def get_google_user_info(self, access_token: str) -> Optional[Dict[str, Any]]:
        """Get user info from Google using access token"""
        user_info_url = "https://www.googleapis.com/oauth2/v2/userinfo"
        headers = {"Authorization": f"Bearer {access_token}"}
        
        try:
            response = requests.get(user_info_url, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.RequestException:
            return None
    
    def handle_oauth_login(self, code: str) -> Optional[Dict[str, Any]]:
        """Handle OAuth2 login flow"""
        # Exchange code for token
        token_data = self.exchange_code_for_token(code)
        if not token_data:
            return None
        
        # Get user info
        user_info = self.get_google_user_info(token_data["access_token"])
        if not user_info:
            return None
        
        # Create or get user
        username = user_info.get("email", "").split("@")[0]
        if username not in self.users_db:
            self.create_user(
                username=username,
                password="",  # No password for OAuth users
                full_name=user_info.get("name", "")
            )
        
        # Create access token
        access_token = self.create_access_token(
            data={"sub": username, "full_name": user_info.get("name", "")}
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "username": username,
                "full_name": user_info.get("name", ""),
                "email": user_info.get("email", "")
            }
        }
    
    def handle_login(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Handle regular login"""
        user = self.authenticate_user(username, password)
        if not user:
            return None
        
        access_token = self.create_access_token(
            data={"sub": user["username"], "full_name": user["full_name"]}
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "username": user["username"],
                "full_name": user["full_name"]
            }
        }
    
    def get_current_user(self, token: str) -> Optional[Dict[str, Any]]:
        """Get current user from token"""
        payload = self.verify_token(token)
        if payload is None:
            return None
        
        username: str = payload.get("sub")
        if username is None:
            return None
        
        user = self.get_user(username)
        if user is None:
            return None
        
        return {
            "username": user["username"],
            "full_name": user["full_name"],
            "disabled": user["disabled"]
        }

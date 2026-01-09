"""
Authentication Service - Handles user authentication with OAuth2 and JWT
"""
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import os
import httpx
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

# Database Service Configuration
DATABASE_SERVICE_URL = os.getenv("DATABASE_SERVICE_URL", "http://database-service:8002")

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """Service for handling authentication operations"""
    
    def __init__(self):
        # In-memory user database (in production, use a real database)
        # self.users_db: Dict[str, Dict[str, Any]] = {}
        print("AuthService initialized")

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Hash a password (bcrypt max 72 bytes)"""
        # Truncate if longer than 72 bytes (bcrypt limit)
        if len(password.encode()) > 72:
            password = password[:72]
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
    
    async def create_user(self, username: str, password: str, full_name: Optional[str] = None) -> Dict[str, Any]:
        """Create user in database-service"""
        payload = {
            "username": username,
            "full_name": full_name or username,
            "hashed_password": self.get_password_hash(password)
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(f"{DATABASE_SERVICE_URL}/users", json=payload, timeout=10.0)
            if resp.status_code == 400:
                raise HTTPException(status_code=400, detail=resp.text)
            resp.raise_for_status()
            return resp.json()

    async def get_user(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user (including hashed_password) from database-service"""
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{DATABASE_SERVICE_URL}/users/username/{username}", timeout=10.0)
            if resp.status_code == 404:
                return None
            resp.raise_for_status()
            return resp.json()

    async def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate a user with username and password via database-service"""
        user = await self.get_user(username)
        if not user:
            return None
        if not self.verify_password(password, user.get("hashed_password", "")):
            return None
        return user

    async def handle_login(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Handle login"""
        user = await self.authenticate_user(username, password)
        if not user:
            return None
        access_token = self.create_access_token(
            data={"sub": user["username"], "full_name": user.get("full_name", "")}
        )
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "username": user["username"],
                "full_name": user.get("full_name", "")
            }
        }

    async def get_current_user(self, token: str) -> Optional[Dict[str, Any]]:
        """Get current user from token (async)"""
        payload = self.verify_token(token)
        if payload is None:
            return None
        username: str = payload.get("sub")
        if username is None:
            return None
        user = await self.get_user(username)
        if user is None:
            return None
        return {
            "username": user["username"],
            "full_name": user.get("full_name", ""),
            "disabled": user.get("disabled", False)
        }

from typing import Optional
from src.core import security
from src.core import exceptions as exc
from src.schemas.user import UserCreate, User
from src.schemas.token import Token
from src.infrastructure.user_client import UserRemoteRepository

class AuthService:
    def __init__(self, user_repo: UserRemoteRepository):
        self.user_repo = user_repo

    async def authenticate_user(self, username: str, password: str) -> Token:
        """
        Verifies username/password and returns a JWT Token.
        Return InvalidCredentials Exceptions if fails.
        """
        # 1. Retrieves the user from DB
        user_data = await self.user_repo.get_user_by_username(username)
        
        if not user_data:
            raise exc.InvalidCredentials("User not found")

        # 2. Verifies the password
        if not security.verify_password(password, user_data["hashed_password"]):
            raise exc.InvalidCredentials("Incorrect password")
            
        # 3. Checks if user is active
        if user_data.get("disabled"):
            raise exc.InvalidCredentials("User is inactive")

        # 4. Create the JWT Token
        access_token = security.create_access_token(
            subject=user_data["username"],
            extra_claims={"full_name": user_data.get("full_name")}
        )
        
        # 5. Returns Toeken schema
        return Token(
            access_token=access_token,
            token_type="bearer",
            user=User(**user_data)
        )

    async def register_new_user(self, user_in: UserCreate) -> User:
        """
        Register new user with hashed password.
        """
        # 1. Checks user existence in DB
        existing_user = await self.user_repo.get_user_by_username(user_in.username)
        if existing_user:
            raise exc.UserAlreadyExists(f"Username {user_in.username} already taken")

        # 2. password hashing
        hashed_pw = security.get_password_hash(user_in.password)

        # 3. Create user in DB
        created_user_data = await self.user_repo.create_user(user_in, hashed_password=hashed_pw)
        
        if not created_user_data:
            raise exc.ServiceUnavailable("Failed to create user in database")

        return User(**created_user_data)
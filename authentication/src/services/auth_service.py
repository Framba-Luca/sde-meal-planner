from datetime import datetime, timezone
from jose import jwt, JWTError
from src.core import security
from src.core.config import settings
from src.core import exceptions as exc
from src.schemas.token import Token
from src.schemas.user import UserCreate, User
from src.infrastructure.user_client import UserRemoteRepository
from src.infrastructure.cache import redis_client

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
        return await self._create_user_token(user_data)

    async def _create_user_token(self, user_data: dict) -> Token:
        username = user_data["username"]

        # Generate duple token (access + refresh)
        access_token = security.create_access_token(subject=username)
        refresh_token = security.create_refresh_token(subject=username)

        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            user=User(**user_data)
        )
    
    async def refresh_access_token(self, refresh_token: str) -> Token:
        """
        Refresh the access token using a valid refresh token.
        """
        try:
            # 1. Decode and validate token type
            payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            if payload.get("type") != "refresh":
                raise exc.InvalidToken("Provided token is not a refresh token")
            
            # 2. Check Blacklist (can raise Redis errors)
            if await redis_client.is_token_revoked(refresh_token):
                raise exc.InvalidToken("Refresh token has been revoked")
            
            # 3. Check User existence (can raise ServiceUnavailable)
            username = payload.get("sub")
            user_data = await self.user_repo.get_user_by_username(username)
            if not user_data:
                raise exc.InvalidToken("User not found")
            
            # 4. Check if user is disabled
            if user_data.get("disabled", False):
                raise exc.InvalidToken("User account is disabled")
            
            # 5. Revoke old refresh token (can raise Redis errors)
            exp = payload.get("exp")
            ttl = int(exp - datetime.now(timezone.utc).timestamp())
            if ttl > 0:
                await redis_client.add_to_blacklist(refresh_token, ttl)

            # 6. Generate new tokens
            return await self._create_user_token(user_data)
            
        except exc.InvalidToken:
            raise  # re-raise InvalidToken as is
        except exc.ServiceUnavailable:
            raise  # re-raise ServiceUnavailable as is
        except JWTError:
            raise exc.InvalidToken("Could not validate refresh token")
        except Exception as e:
            # Catch any other errors (Redis, network, etc.)
            raise exc.ServiceUnavailable(f"Refresh token service error: {str(e)}")

    async def logout(self, token: str) -> None:
        """
        Logout user by revoking the provided token (access or refresh).
        """
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            exp = payload.get("exp")
            ttl = int(exp - datetime.now(timezone.utc).timestamp())
            if ttl > 0:
                await redis_client.add_to_blacklist(token, ttl)
        except JWTError:
            raise exc.InvalidToken("Could not validate token for logout")
        except Exception as e:
            # If Redis fails but token is valid, let it fail gracefully
            # (token will auto-expire anyway)
            raise exc.ServiceUnavailable("Could not revoke token (Redis unavailable)")

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
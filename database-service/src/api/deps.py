from typing import Annotated, Dict, Any, Optional
from fastapi import Header, HTTPException, status, Depends
from jose import jwt, JWTError
import os
from src.core.config import settings

async def verify_token(
    authorization: Annotated[str, Header()] = None
) -> Dict[str, Any]:
    """
    Verifies the JWT validity (signature and expiration only).
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization Header"
        )

    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Auth Scheme"
            )

        # Decode and verify signature using the shared SECRET_KEY
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials (JWT signature failed)"
        )
    except (ValueError, IndexError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format"
        )


# --- 2. Internal Token Verification (Service-to-Service) ---

async def verify_internal_service_token(
    authorization: Annotated[str, Header()] = None
) -> Dict[str, Any]:
    """
    Protects routes used for internal service-to-service communication.
    Uses a shared secret key (INTERNAL_SERVICE_SECRET).
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization Header"
        )

    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Auth Scheme"
            )

        # Retrieve the secret from environment variables
        internal_secret = os.getenv(
            "INTERNAL_SERVICE_SECRET",
            "internal-service-secret-key"
        )

        # Direct comparison
        if token != internal_secret:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid internal service token"
            )

        return {"service": "internal", "authenticated": True}

    except (ValueError, IndexError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format"
        )

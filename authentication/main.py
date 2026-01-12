from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.config import settings
from src.core import exceptions as exc
from src.api.v1.router import api_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.FRONTEND_URL,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
)

# --- Exception Handlers ---
@app.exception_handler(exc.InvalidCredentials)
async def invalid_credentials_handler(request: Request, exc: exc.InvalidCredentials):
    return JSONResponse(
        status_code=401,
        content={"detail": str(exc)},
        headers={"WWW-Authenticate": "Bearer"},
    )

@app.exception_handler(exc.UserAlreadyExists)
async def user_exists_handler(request: Request, exc: exc.UserAlreadyExists):
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)},
    )

@app.exception_handler(exc.ServiceUnavailable)
async def service_unavailable_handler(request: Request, exc: exc.ServiceUnavailable):
    return JSONResponse(
        status_code=503,
        content={"detail": "Service temporarily unavailable, please try again later."},
    )

# --- Include Routers ---
app.include_router(api_router, prefix=settings.API_V1_STR)

# --- Health Check ---
@app.get("/health")
def health_check():
    return {"status": "healthy", "service": settings.PROJECT_NAME}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
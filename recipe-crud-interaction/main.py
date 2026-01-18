import uvicorn
from fastapi import FastAPI
from src.core.config import settings
from src.api.v1.router import api_router

app = FastAPI(title=settings.PROJECT_NAME, version=settings.VERSION)

@app.get("/health", tags=["System"])
def health():
    return {"status": "ok"}

app.include_router(api_router, prefix=settings.API_V1_STR)

if __name__ == "__main__":
    uvicorn.run("src.main:app", host="0.0.0.0", port=8005, reload=True)
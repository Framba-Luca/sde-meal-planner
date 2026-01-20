from sqlmodel import SQLModel, create_engine, Session
from src.core.config import settings
from typing import Generator
import os

DATABASE_URL = f"postgresql://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
engine = create_engine(DATABASE_URL, echo=os.getenv("DEBUG", True))

def init_db():
    """
    Initializes all the tables in the SQLModel.
    To call at the start of the application.
    """
    SQLModel.metadata.create_all(engine)

def get_session() -> Generator[Session, None, None]:
    """
    Dependency function for FastAPI.
    Opens and closes a session for each request.
    """
    with Session(engine) as session:
        yield session
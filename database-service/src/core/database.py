import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from typing import Generator
from src.core.config import settings

class PostgreSQLAdapter:
    def __init__(self):
        self._pool = None

    def connect(self):
        """Initialize the database connection pool."""
        try:
            self._pool = psycopg2.pool.ThreadedConnectionPool(
                minconn=1,
                maxconn=20,
                host=settings.DB_HOST,
                port=settings.DB_PORT,
                dbname=settings.DB_NAME,
                user=settings.DB_USER,
                password=settings.DB_PASSWORD
            )
            print("Database connection pool created successfully.")
        except Exception as e:
            print(f"Error connecting to database: {e}")
            raise e

    def disconnect(self):
        """Closes all the connection."""
        if self._pool:
            self._pool.closeall()
            print("Database connection pool closed.")

    @contextmanager
    def get_cursor(self) -> Generator:
        """
        Context manager to obtain a cursor from the pool.
        Handles commit & rollback automatically.
        """
        if not self._pool:
            raise Exception("Database pool not initialized. Call connect() first.")
            
        conn = self._pool.getconn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                yield cur
                conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            self._pool.putconn(conn)

# Singleton instance
db_adapter = PostgreSQLAdapter()
"""
Database Connection Management

Handles SQLite and PostgreSQL connections with proper pooling and configuration.
Provides context manager for safe database session handling with automatic cleanup.

Database Configuration:
    - Uses environment variable DATABASE_URL or defaults to PostgreSQL
    - Automatically handles SQLite relative paths
    - Applies pool optimization per database type
    - Supports both development and production configurations
"""
from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Generator
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, Engine, inspect, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool, QueuePool

from .models import Base
from constants import DB_ECHO_SQL, DB_POOL_SIZE, DB_MAX_OVERFLOW, DB_POOL_RECYCLE

load_dotenv()


# ============================================================================
# DATABASE CONFIGURATION
# ============================================================================

class DatabaseConfig:
    """Database configuration constants and defaults"""
    
    # Default database URLs
    DEFAULT_POSTGRESQL_URL = (
        "postgresql://postgres:password@localhost:5432/skills_trend_db"
    )
    DEFAULT_SQLITE_PATH = "sqlite:///./skills_trend.db"
    
    # Connection settings
    SQLITE_TIMEOUT = 15
    POSTGRES_POOL_SIZE = DB_POOL_SIZE
    POSTGRES_MAX_OVERFLOW = DB_MAX_OVERFLOW
    POSTGRES_POOL_RECYCLE = DB_POOL_RECYCLE
    ECHO_SQL = DB_ECHO_SQL  # Set True for debugging SQL queries


# ============================================================================
# DATABASE INITIALIZATION
# ============================================================================

def _get_database_url() -> str:
    """
    Get database URL from environment or use default.
    
    Priority:
        1. DATABASE_URL environment variable
        2. Default PostgreSQL URL
    
    For SQLite paths that are relative, converts them to absolute paths
    based on project root directory.
    
    Returns:
        Complete database connection URL
        
    Example:
        >>> url = _get_database_url()
        >>> url.startswith(("sqlite://", "postgresql://"))
        True
    """
    url = os.getenv("DATABASE_URL", DatabaseConfig.DEFAULT_POSTGRESQL_URL)
    
    # Handle relative SQLite paths - convert to absolute
    if url.startswith("sqlite:///") and ":" not in url.split("sqlite:///")[1]:
        relative_path = url.replace("sqlite:///", "")
        project_root = Path(__file__).resolve().parent.parent.parent
        url = f"sqlite:///{project_root / relative_path}"
    
    return url


def _create_engine(database_url: str) -> Engine:
    """
    Create SQLAlchemy engine with appropriate settings for database type.
    
    Configuration varies by database:
    - SQLite: Uses StaticPool (single connection), no connection pooling
    - PostgreSQL: Uses QueuePool with configured pool size and overflow
    
    Args:
        database_url: Database connection URL string
        
    Returns:
        Configured SQLAlchemy engine instance
        
    Raises:
        sqlalchemy.exc.ArgumentError: If database URL is invalid
        
    Example:
        >>> engine = _create_engine("sqlite:///test.db")
        >>> engine.url.drivername
        'sqlite'
    """
    if database_url.startswith("sqlite"):
        return create_engine(
            database_url,
            connect_args={
                "check_same_thread": False,
                "timeout": DatabaseConfig.SQLITE_TIMEOUT
            },
            poolclass=StaticPool,
            echo=DatabaseConfig.ECHO_SQL,
        )
    else:
        # PostgreSQL with optimized pooling
        return create_engine(
            database_url,
            poolclass=QueuePool,
            pool_size=DatabaseConfig.POSTGRES_POOL_SIZE,
            max_overflow=DatabaseConfig.POSTGRES_MAX_OVERFLOW,
            pool_pre_ping=True,  # Verify connections before using
            pool_recycle=DatabaseConfig.POSTGRES_POOL_RECYCLE,
            echo=DatabaseConfig.ECHO_SQL,
        )


# ============================================================================
# SINGLETON DATABASE ENGINE & SESSION FACTORY
# ============================================================================

DATABASE_URL: str = _get_database_url()
engine: Engine = _create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ============================================================================
# DATABASE OPERATIONS
# ============================================================================

def init_db() -> None:
    """
    Initialize database tables based on SQLAlchemy models.
    
    Creates all tables defined in Base.metadata if they don't already exist.
    Safe to call multiple times - idempotent operation.
    
    Raises:
        sqlalchemy.exc.OperationalError: If database connection fails
        
    Example:
        >>> init_db()
        >>> # Tables are now ready for use
    """
    Base.metadata.create_all(bind=engine)
    _ensure_job_status_column()
    _ensure_job_company_url_column()
    print("Database tables initialized successfully")


def _ensure_job_status_column() -> None:
    """Add job extraction status column for existing databases."""
    inspector = inspect(engine)
    if not inspector.has_table("jobs"):
        return

    columns = {column["name"] for column in inspector.get_columns("jobs")}
    if "status_ekstraksi" in columns:
        return

    if engine.url.drivername.startswith("sqlite"):
        ddl = (
            "ALTER TABLE jobs ADD COLUMN status_ekstraksi VARCHAR(20) "
            "NOT NULL DEFAULT 'pending'"
        )
    else:
        ddl = (
            "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS status_ekstraksi "
            "VARCHAR(20) NOT NULL DEFAULT 'pending'"
        )

    with engine.connect() as connection:
        connection.execute(text(ddl))
        connection.execute(
            text("UPDATE jobs SET status_ekstraksi = 'pending' WHERE status_ekstraksi IS NULL")
        )
        connection.commit()


def _ensure_job_company_url_column() -> None:
    """Add job company_url column for existing databases."""
    inspector = inspect(engine)
    if not inspector.has_table("jobs"):
        return

    columns = {column["name"] for column in inspector.get_columns("jobs")}
    if "company_url" in columns:
        return

    if engine.url.drivername.startswith("sqlite"):
        ddl = "ALTER TABLE jobs ADD COLUMN company_url VARCHAR(500)"
    else:
        ddl = "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS company_url VARCHAR(500)"

    with engine.connect() as connection:
        connection.execute(text(ddl))
        connection.commit()


@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """
    Context manager for safe database session handling.
    
    Automatically commits changes upon successful execution of the block,
    rolls back the transaction on exception, and always closes the session.
    
    Yields:
        SQLAlchemy Session instance
        
    Raises:
        Exception: Re-raises any exception that occurs during block execution
        
    Example:
        >>> with get_db_context() as db:
        ...     user = db.query(User).filter(User.id == 1).first()
        ...     db.add(new_record)
        ...     # Commit is handled automatically upon exit, or you can call db.commit() explicitly
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency injection provider for FastAPI endpoints.
    
    Use this in FastAPI route dependencies to get a database session.
    Session is automatically managed by FastAPI dependency system.
    
    Yields:
        SQLAlchemy Session instance
        
    Example:
        >>> from fastapi import Depends
        >>> @app.get("/users")
        ... def get_users(db: Session = Depends(get_db)):
        ...     return db.query(User).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()




if __name__ == "__main__":
    print("Initializing database...")
    init_db()

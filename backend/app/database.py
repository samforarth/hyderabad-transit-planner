"""
Database connection and session management module.

This module sets up the synchronous SQLAlchemy engine and session factory.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import settings

# Create the synchronous SQLAlchemy engine
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)

# SessionLocal is the factory for new Session objects
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for our ORM models to inherit from
Base = declarative_base()


def get_db():
    """
    Dependency generator for FastAPI to manage database sessions.
    
    We use dependency injection here so that FastAPI automatically creates a 
    new database session for each request and ensures it is closed when the 
    request finishes (even if there was an error). This prevents connection leaks.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import NullPool
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://user:password@localhost:5432/trading_dashboard"
)

# Create engine
engine = create_engine(
    DATABASE_URL,
    poolclass=NullPool,  # Disable connection pooling for better control
    echo=os.getenv("DEBUG", "false").lower() == "true"
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db():
    """Dependency for getting DB session in routes"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

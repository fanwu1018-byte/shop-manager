import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from database.models import Base

DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
DB_PATH = os.path.join(DB_DIR, "shop.db")


def init_db():
    """Initialize the database: create directory, engine, and all tables."""
    os.makedirs(DB_DIR, exist_ok=True)
    engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)
    Base.metadata.create_all(engine)
    return engine


def get_session() -> Session:
    """Create and return a new database session."""
    engine = init_db()
    Session = sessionmaker(bind=engine)
    return Session()
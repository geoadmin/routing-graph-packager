import os

from sqlmodel import create_engine, Session

from .config import SETTINGS

engine = create_engine(SETTINGS.SQLALCHEMY_DATABASE_URI, echo=bool(os.getenv("DEBUG")), future=True)


def get_db():
    """Gets a DB Session."""
    db = Session(engine, autocommit=False, autoflush=False)
    try:
        yield db
    finally:
        db.close()

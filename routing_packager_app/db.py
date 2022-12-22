import os

from sqlmodel import create_engine, Session

from .config import SETTINGS as S

SQLALCHEMY_DATABASE_URI: str = f"postgresql://{S.POSTGRES_USER}:{S.POSTGRES_PASS}@{S.POSTGRES_HOST}:{S.POSTGRES_PORT}/{S.POSTGRES_DB}"

engine = create_engine(SQLALCHEMY_DATABASE_URI, echo=bool(os.getenv("DEBUG")), future=True)


def get_db():
    """Gets a DB Session."""
    db = Session(engine, autocommit=False, autoflush=False)
    try:
        yield db
    finally:
        db.close()

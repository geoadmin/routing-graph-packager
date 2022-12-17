import os

from sqlmodel import create_engine

from .config import SETTINGS

engine = create_engine(SETTINGS.SQLALCHEMY_DATABASE_URI, echo=bool(os.getenv("DEBUG")), future=True)

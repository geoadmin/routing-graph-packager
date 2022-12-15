from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker

from routing_packager_app import SETTINGS

engine = create_engine(SETTINGS.SQLALCHEMY_DATABASE_URI, echo=True, future=True)
SessionLocal = sessionmaker(autoflush=False, autocommit=False, bind=engine)

from datetime import datetime
from typing import Optional, List

from fastapi.security import HTTPBasicCredentials
from geoalchemy2 import Geography
from pydantic import EmailStr
from sqlalchemy import Column
from sqlalchemy_utils import PasswordType
from sqlmodel import SQLModel, Field, DateTime, Relationship, Session, select

from ..config import SETTINGS
from ..constants import Providers, Statuses
from ..utils.geom_utils import wkbe_to_str


class JobBase(SQLModel):
    name: str = Field(nullable=False, default="test")
    provider: Providers = Field(nullable=False, default=Providers.OSM)
    # WKBElement isn't a valid pydantic type
    bbox: str = Field(
        sa_column=Column(Geography("POLYGON", srid=4326, spatial_index=True, nullable=False)),
        default="5.9559,45.818,10.4921,47.8084",
    )
    description: str = Field(nullable=True, default="")
    update: bool = Field(nullable=False, default=False)


class JobRead(JobBase):
    id: int = 1
    user_id: int = 1
    arq_id: str = ""
    status: Statuses = Statuses.QUEUED
    bbox: str = ""
    zip_path: Optional[str]
    last_started: Optional[datetime]
    last_finished: Optional[datetime]


class JobCreate(JobBase):
    pass


class Job(JobBase, table=True):

    __tablename__ = "jobs"

    id: Optional[int] = Field(primary_key=True)
    arq_id: Optional[str] = Field(nullable=True)
    user_id: int = Field(default=None, foreign_key="users.id")
    status: Statuses = Field(nullable=False)
    zip_path: str = Field(nullable=True)
    last_started: Optional[datetime] = Field(nullable=True)  # did it ever run?
    last_finished: Optional[datetime] = Field(
        sa_column=Column(DateTime(), nullable=True)
    )  # did it ever finish?

    user: "User" = Relationship(back_populates="jobs")

    def __repr__(self):  # pragma: no cover
        s = f"<Job id={self.id} name={self.name} status={self.status} provider={self.provider}>"
        return s

    def convert_bbox(self):
        """Converts a WKBElement to a bbox string"""
        self.bbox = wkbe_to_str(self.bbox)


class UserBase(SQLModel):
    email: EmailStr = Field(index=True, unique=True, nullable=False)


class UserRead(UserBase):
    id: int


class UserCreate(UserBase):
    password: str


class User(UserBase, table=True):
    """The users table."""

    __tablename__ = "users"

    id: Optional[int] = Field(primary_key=True)
    password: str = Field(sa_column=Column(PasswordType(schemes=("pbkdf2_sha512",)), nullable=False))
    jobs: List[Job] = Relationship(back_populates="user")

    def __repr__(self):  # pragma: no cover
        return "<User {}>".format(self.email)

    @staticmethod
    def get_user(db: Session, auth_data: HTTPBasicCredentials) -> Optional["User"]:
        user = db.exec(select(User).filter(User.email == auth_data.username)).first()
        if not user:
            return None
        if not user.password == auth_data.password:
            return None

        return user

    @staticmethod
    def add_admin_user(session: Session):
        """Add admin user before first request."""
        admin_email = SETTINGS.ADMIN_EMAIL
        admin_pass = SETTINGS.ADMIN_PASS

        if not session.exec(select(User).filter_by(email=admin_email)).first():
            admin_user = User(email=admin_email, password=admin_pass)
            session.add(admin_user)
            session.commit()

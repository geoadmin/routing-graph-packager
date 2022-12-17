from datetime import datetime
from typing import Optional, List

from fastapi.security import HTTPBasicCredentials
from geoalchemy2 import Geography
from pydantic import EmailStr
from sqlalchemy import Column
from sqlalchemy_utils import PasswordType
from sqlmodel import SQLModel, Field, DateTime, Relationship, Session, select

from routing_packager_app.constants import Routers, Providers, Compressions, Statuses


class JobBase(SQLModel):
    name: str = Field(nullable=False, default="test")
    router: Routers = Field(
        nullable=False, default=Routers.VALHALLA
    )  # router name, i.e. valhalla, graphhopper, ors etc
    provider: Providers = Field(nullable=False, default=Providers.OSM)
    compression: Compressions = Field(nullable=False, default=Compressions.ZIP)  # zip, tar etc
    bbox: str = Field(
        sa_column=Column(Geography("POLYGON", srid=4326, spatial_index=True, nullable=False)),
        default="5.9559,45.818,10.4921,47.8084",
    )
    description: str = Field(nullable=True)


class JobRead(JobBase):
    id: int
    user_id: int
    arq_id: str
    status: str
    last_started: datetime
    last_finished: datetime


class JobCreate(JobBase):
    pass


class Job(JobBase, table=True):

    __tablename__ = "jobs"

    id: Optional[int] = Field(primary_key=True)
    arq_id: Optional[str] = Field(nullable=True)
    user_id: int = Field(default=None, foreign_key="users.id")
    status: Statuses = Field(nullable=False)
    last_started: Optional[datetime] = Field(nullable=True)  # did it ever run?
    last_finished: Optional[datetime] = Field(
        sa_column=Column(DateTime(), nullable=True)
    )  # did it ever finish?

    user: "User" = Relationship(back_populates="jobs")

    def __repr__(self):  # pragma: no cover
        s = f"<Job id={self.id} name={self.name} status={self.status} provider={self.provider} router={self.router} compression={self.compression}>"
        return s


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

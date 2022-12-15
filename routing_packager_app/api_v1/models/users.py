import base64
from typing import List, Optional

from pydantic import EmailStr, BaseModel
from sqlalchemy import Column
from sqlalchemy_utils.types import PasswordType
from sqlmodel import SQLModel, Field, Relationship

from .jobs import JobSql
from ... import db


class UserSql(SQLModel, table=True):
    """The users table."""

    __tablename__ = "users"

    id: int = Field(primary_key=True)
    email: EmailStr = Field(index=True, unique=True, nullable=False)
    password = Field(sa_column=Column(PasswordType(schemes=("pbkdf2_sha512",)), nullable=False))
    tasks: List[JobSql] = Relationship(back_populates="user")

    def __repr__(self):  # pragma: no cover
        return "<User {}>".format(self.email)

    @staticmethod
    def get_user_id(auth_data) -> Optional[int]:
        decoded = base64.b64decode(auth_data).decode("ascii")
        username, password = decoded.split(":")

        user = UserSql.query.filter("email" == username)
        if not user:
            return None
        if not user.password == password:
            return None

        return user.id


class UserResponse(BaseModel):
    id: int
    email: int

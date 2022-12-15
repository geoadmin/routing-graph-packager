from datetime import datetime
from typing import Optional

from geoalchemy2 import Geography
from pydantic import BaseModel
from sqlalchemy import Column
from sqlmodel import SQLModel, Field, DateTime


class JobSql(SQLModel, table=True):

    __tablename__ = "jobs"

    id: int = Field(default=None, primary_key=True)
    user_id: int = Field(default=None, foreign_key="user.id")
    rq_id: str = Field(nullable=True)
    name: str = Field(nullable=False)
    description: str = Field(nullable=True)
    status: str = Field(nullable=False)
    provider: str = Field(nullable=False)
    router: str = Field(nullable=False)  # router name, i.e. valhalla, graphhopper, ors etc
    bbox: str = Field(sa_column=Column(Geography("POLYGON", srid=4326, spatial_index=True, nullable=False)))
    compression: str = Field(nullable=False)  # zip, tar etc
    last_started: datetime = Field(nullable=False)  # did it ever run?
    last_finished: datetime = Field(sa_column=Column(DateTime(), nullable=True))  # did it ever finish?

    def __repr__(self):  # pragma: no cover
        s = f"<Job id={self.id} name={self.name} status={self.status} provider={self.provider} router={self.router} compression={self.compression}>"
        return s

    def set_status(self, status: str):
        self.status = status

    def set_rq_id(self, rq_id: str):  # pragma: no cover
        self.rq_id = rq_id

    def set_last_finished(self, dt: datetime):
        self.last_finished = dt


class JobResponse(BaseModel):
    id: int
    user_id: int
    rq_id: int
    status: str
    last_started: datetime
    last_finished: datetime

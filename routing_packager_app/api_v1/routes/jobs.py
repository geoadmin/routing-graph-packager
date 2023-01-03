import os
from shutil import rmtree
from typing import List, Optional

from arq.connections import ArqRedis
from arq.constants import job_key_prefix
from fastapi import Depends, HTTPException, APIRouter
from fastapi.security import HTTPBasicCredentials
from starlette.requests import Request
from starlette.responses import Response
from starlette.status import (
    HTTP_401_UNAUTHORIZED,
    HTTP_409_CONFLICT,
    HTTP_204_NO_CONTENT,
    HTTP_404_NOT_FOUND,
)

from sqlalchemy import func
from sqlmodel import Session, select

from ..models import JobRead, JobCreate, Job, User
from ..dependencies import split_bbox, get_validated_name, validate_bbox
from ...utils.db_utils import delete_or_abort, add_or_abort
from ...db import get_db
from ...config import SETTINGS, TestSettings
from ...auth.basic_auth import BasicAuth
from ...utils.geom_utils import bbox_to_wkt
from ...utils.file_utils import make_package_path
from ...constants import *

router = APIRouter()


@router.get("/", response_model=List[JobRead])
async def get_jobs(
    provider: Optional[Providers] = None,
    status: Optional[Statuses] = None,
    update: bool = None,
    bbox: List[float] = Depends(split_bbox),
    db: Session = Depends(get_db),
):
    filters = []
    if bbox:
        filters.append(func.ST_Intersects(Job.bbox, bbox_to_wkt(bbox)))
    if provider:
        filters.append(Job.provider == provider)
    if status:
        filters.append(Job.status == status)
    if update is not None:
        filters.append(Job.update == update)

    jobs = db.exec(select(Job).filter(*filters)).all()
    for job in jobs:
        job.convert_bbox()

    return jobs


@router.post("/", response_model=JobRead)
async def post_job(
    req: Request,
    job: JobCreate,
    db: Session = Depends(get_db),
    auth: HTTPBasicCredentials = Depends(BasicAuth),
):
    """POST a new job. Needs admin privileges."""
    # Sanitize the name field before using it
    job.name = get_validated_name(job.name)
    current_user = User.get_user(db, auth)
    if not current_user:
        raise HTTPException(HTTP_401_UNAUTHORIZED, "No valid username or password provided.")

    # keep the input bbox string around for the response
    validate_bbox(job.bbox)
    bbox_str = job.bbox
    job.bbox = bbox_to_wkt(split_bbox(bbox_str))

    try:
        zip_path = make_package_path(SETTINGS.DATA_DIR, job.name, job.provider.lower())
        arq_id = zip_path.stem
    except FileExistsError:
        raise HTTPException(HTTP_409_CONFLICT, "Already registered this package.")

    # add to DB and the things we couldn't set yet
    db_job = Job(
        **job.__dict__,
    )
    db_job.status = Statuses.QUEUED
    db_job.arq_id = arq_id
    db_job.user_id = current_user.id
    db_job.zip_path = str(zip_path.resolve())
    add_or_abort(db, db_job)

    # launch Redis task and update db entries there
    # when testing, we test the create_package function directly
    if not isinstance(SETTINGS, TestSettings):  # pragma: no cover
        pool: ArqRedis = req.app.state.redis_pool
        await pool.enqueue_job(
            "create_package",
            db_job.id,
            db_job.arq_id,
            db_job.description,
            bbox_str,
            str(zip_path.resolve()),
            current_user.id,
            _job_id=db_job.arq_id,
        )

    # At this point it'd be a geoalchemy2.WKBElement but the output model requires a string
    db_job.convert_bbox()
    return db_job


@router.get("/{job_id}", response_model=JobRead)
async def get_job(job_id: int, db: Session = Depends(get_db)):
    """GET a single job."""
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(HTTP_404_NOT_FOUND, f"Couldn't find job id {job_id}")

    job.convert_bbox()

    return job


@router.delete("/{job_id}")
async def delete_job(
    req: Request,
    job_id: int,
    db: Session = Depends(get_db),
    auth: HTTPBasicCredentials = Depends(BasicAuth),
):
    """DELETE a single job. Will also stop the job if it's in progress. Needs admin privileges."""
    # first authenticate
    req_user = User.get_user(db, auth)
    if not req_user:
        raise HTTPException(HTTP_401_UNAUTHORIZED, "Not authorized to delete a user.")

    # get job or 404
    db_job: Job = db.get(Job, job_id)
    if not db_job:
        raise HTTPException(HTTP_404_NOT_FOUND, f"Couldn't find job id {job_id}")

    if not isinstance(SETTINGS, TestSettings):  # pragma: no cover
        job_arq_id: str = job_key_prefix + db_job.arq_id
        pool: ArqRedis = req.app.state.redis_pool
        # try to delete the Redis job or don't care if there is none
        if pool.keys(job_arq_id):
            await pool.delete(job_arq_id)

    delete_or_abort(db, db_job)
    dir_path = os.path.dirname(db_job.zip_path)
    if os.path.exists(dir_path):
        rmtree(dir_path)

    return Response("", HTTP_204_NO_CONTENT)

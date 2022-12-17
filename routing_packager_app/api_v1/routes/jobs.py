import os
from typing import List, Optional, Union

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
from ..dependencies import split_bbox, validate_name
from ...utils.db_utils import get_db, delete_or_abort, add_or_abort
from ...config import SETTINGS, TestSettings
from ...auth.basic_auth import BasicAuth
from ...utils.geom_utils import bbox_to_wkt
from ...utils.file_utils import make_package_path
from ...constants import *
from ...tasks import create_package

router = APIRouter()


@router.get("/jobs", response_model=List[JobRead])
def get_jobs(
    router: Optional[Routers] = Routers.VALHALLA,
    provider: Optional[Providers] = Providers.OSM,
    status: Optional[Statuses] = Statuses.QUEUED,
    compression: Optional[Compressions] = Compressions.ZIP,
    bbox: Union[List[float], None] = Depends(split_bbox),
    db: Session = Depends(get_db),
):
    filters = []
    if bbox:
        filters.append(func.ST_Intersects(Job.bbox, bbox_to_wkt(bbox)))
    if router:
        filters.append((Job.router == router))
    if provider:
        filters.append(Job.provider == provider)
    if status:
        filters.append(Job.status == status)
    if compression:
        filters.append(Job.compression == compression)

    return db.exec(select(Job).filter(*filters)).all()


@router.post("/", response_model=JobRead)
def post_job(
    req: Request,
    job: JobCreate,
    db: Session = Depends(get_db),
    auth: HTTPBasicCredentials = Depends(BasicAuth),
):
    """POST a new job. Needs admin privileges."""
    # Sanitize the name field before using it
    job.name = validate_name(job.name)
    current_user = User.get_user(db, auth)
    if not current_user:
        raise HTTPException(HTTP_401_UNAUTHORIZED, "No valid username or password provided.")

    job.bbox = bbox_to_wkt(split_bbox(job.bbox))

    try:
        result_path = make_package_path(
            SETTINGS.DATA_DIR,
            job.name,
            job.router.lower(),
            job.provider.lower(),
            job.compression.lower(),
        )
    except FileExistsError:
        raise HTTPException(HTTP_409_CONFLICT, "Already registered this package.")

    # add to DB
    db_job = Job(
        **job.__dict__,
    )
    db_job.status = Statuses.QUEUED.lower()
    db_job.user_id = current_user.id
    add_or_abort(db, db_job)

    # launch Redis task and update db entries there
    # for testing we don't want that behaviour
    pool: ArqRedis = req.app.state.redis_pool
    if not isinstance(SETTINGS, TestSettings):  # pragma: no cover
        pool.enqueue(
            create_package,
            db_job.id,
            db_job.description,
            db_job.router,
            db_job.provider,
            db_job.bbox,
            result_path,
            db_job.compression,
            current_user.id,
            _job_id=result_path.stem,
        )

    return db_job


@router.get("/{job_id}", response_model=JobRead)
def get_job(job_id: int, db: Session = Depends(get_db)):
    """GET a single job."""
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(HTTP_404_NOT_FOUND, f"Couldn't find job id {job_id}")

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

    job_arq_id: str = job_key_prefix + db_job.arq_id
    pool: ArqRedis = req.app.redis_pool
    # try to delete the Redis job or don't care if there is none
    if pool.keys(job_arq_id):
        await pool.delete(job_arq_id)

    delete_or_abort(db, db_job)
    if os.path.exists(db_job.arq_id):
        os.remove(db_job.arq_id)

    return Response("", HTTP_204_NO_CONTENT)

from datetime import datetime
from enum import Enum
import os
import json
from typing import List, Optional

from fastapi import Query, Depends, HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from starlette.requests import Request
from starlette.status import HTTP_401_UNAUTHORIZED

from flask import current_app, g
from flask_restx import Resource, Namespace, reqparse, abort
from flask_restx.errors import HTTPStatus
from sqlalchemy import func
from sqlalchemy.orm import Session
from rq.registry import NoSuchJobError
from rq.job import Job as RqJob
from sqlalchemy.orm import sessionmaker

from . import router
from ..models.jobs import JobSql, JobResponse
from .validate import validate_post, validate_get
from .schemas import job_base_schema, job_response_schema, osm_response_schema
from ..dependencies import split_bbox, get_db, validate_name
from ..models.users import UserSql
from ... import SETTINGS
from ...auth.basic_auth import BasicAuth
from ...db import SessionLocal
from ...utils.db_utils import add_or_abort, delete_or_abort
from ...utils.geom_utils import bbox_to_wkt
from ...utils.file_utils import make_package_path
from ...osmium import fileinfo_proc
from ...constants import *


@router.get("/jobs", response_model=List[JobResponse])
async def get_job(
    router: Optional[Routers],
    provider: Optional[Providers],
    status: Optional[Statuses],
    compression: Optional[Compressions],
    bbox: Optional[List[float]] = Depends(split_bbox),
    db: Session = Depends(get_db)
):
    filters = []
    if bbox:
        filters.append(func.ST_Intersects(JobSql.bbox, bbox_to_wkt(bbox)))
    if router:
        filters.append((JobSql.router == router))
    if provider:
        filters.append(JobSql.provider == provider)
    if status:
        filters.append(JobSql.status == status)
    if compression:
        filters.append(JobSql.compression == compression)

    return db.query(JobSql).filter(*filters).all()


@router.post("/", response_model=JobResponse)
async def post(
    req: Request,
    name: str = Depends(validate_name),
    router: Optional[Routers] = Query(...),
    provider: Optional[Providers] = Query(...),
    compression: Optional[Compressions] = Query(default=Compressions.ZIP),
    bbox: Optional[List[float]] = Depends(split_bbox),
    description: Optional[str] = None,
    db: Session = Depends(get_db),
    auth: HTTPBasicCredentials = Depends(BasicAuth)
):
    """POST a new job. Needs admin privileges."""

    # avoid circular imports
    from ...tasks import create_package

    # Sanitize the name field a little
    name = name.replace(" ", "_")
    current_user_id = UserSql.get_user_id(auth)
    if not current_user_id:
        raise HTTPException(HTTP_401_UNAUTHORIZED, "No valid username or password provided.")

    result_path = make_package_path(SETTINGS.DATA_DIR, name, router, provider, compression)

    job = JobSql(
        name=name,
        description=description,
        provider=provider,
        router=router,
        user_id=current_user_id,
        status="Queued",
        compression=compression,
        bbox=bbox_to_wkt(bbox),
        path=result_path,
        last_started=datetime.utcnow(),
    )

    db.add(job)
    db.commit()

    # launch Redis task and update db entries there
    # for testing we don't want that behaviour
    if not current_app.testing:  # pragma: no cover
        current_app.task_queue.enqueue(
            create_package,
            job.id,
            description,
            router,
            provider,
            bbox,
            result_path,
            compression,
            current_user_id,
            current_app.config["FLASK_CONFIG"],
        )

    return job


@ns.route("/<int:id>")
@ns.response(HTTPStatus.INTERNAL_SERVER_ERROR, "Unknown error.")
@ns.response(HTTPStatus.NOT_FOUND, "Unknown job id.")
class JobSingle(Resource):
    """Get or delete single jobs"""

    @ns.marshal_with(job_response_model)
    def get(self, id):
        """GET a single job."""
        return JobSql.query.get_or_404(id)

    @basic_auth.login_required
    @ns.doc(security="basic")
    @ns.response(HTTPStatus.NO_CONTENT, "Success, no content.")
    @ns.response(HTTPStatus.FORBIDDEN, "Access forbidden.")
    @ns.response(HTTPStatus.UNAUTHORIZED, "Invalid/missing basic authorization.")
    def delete(self, id):
        """DELETE a single job. Will also stop the job if it's in progress. Needs admin privileges."""
        db_job: JobSql = JobSql.query.get_or_404(id)

        # try to delete the Redis job or don't care if there is none
        try:
            rq_job = RqJob.fetch(db_job.rq_id, connection=current_app.redis)
            if rq_job.get_status() in ("queued", "started"):  # pragma: no cover
                rq_job.delete()
        except NoSuchJobError:
            pass

        delete_or_abort(db_job)
        if os.path.exists(db_job.pbf_path):
            os.remove(db_job.pbf_path)

        return "", HTTPStatus.NO_CONTENT


osm_response_model = ns.model("OsmModel", osm_response_schema)


@ns.route("/<int:id>/data/pbf")
@ns.response(HTTPStatus.INTERNAL_SERVER_ERROR, "Unknown error.")
@ns.response(HTTPStatus.NOT_FOUND, "Unknown job id.")
class OsmSingle(Resource):
    """Interact with a job's OSM file."""

    @ns.marshal_with(osm_response_model)
    def get(self, id):
        """GET info about a job's OSM file."""
        job = JobSql.query.get_or_404(id)
        pbf_path = job.pbf_path

        # Bail if it doesn't exist
        if not os.path.exists(pbf_path):
            abort(code=HTTPStatus.NOT_FOUND, error=f"OSM file for job {job.id} not found.")

        osmium_proc = fileinfo_proc(pbf_path)
        stdout, _ = osmium_proc.communicate()

        # Sanitize osmium's response to relevant fields
        osmium_out = json.loads(stdout)

        response = dict()
        response["filepath"] = osmium_out["file"]["name"]
        response["size"] = osmium_out["file"]["size"]
        response["timestamp"] = osmium_out["header"]["option"]["osmosis_replication_base_url"]

        # Ouput bbox as string like the other endpoints
        bbox = [str(x) for x in osmium_out["header"]["boxes"][0]]
        response["bbox"] = ",".join(bbox)

        return response

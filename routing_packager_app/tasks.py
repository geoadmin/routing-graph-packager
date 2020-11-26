import os
import logging
from datetime import datetime
import json
from typing import List
import shutil

from rq import get_current_job
from rq.job import Job
from flask_sqlalchemy import SessionBase
from werkzeug.exceptions import InternalServerError, HTTPException
from docker.errors import ImageNotFound
from shapely.geometry import Polygon
from osmium.io import Reader

from . import create_app, db
from .api_v1.jobs.models import Job
from .logger import AppSmtpHandler, get_smtp_details
from .routers import get_router
from .utils.file_utils import make_tarfile, make_zipfile
from .utils.geom_utils import bbox_to_geom
from .osmium import get_pbfs_by_area, extract_proc
from .constants import *

LOGGER = logging.getLogger('packager')
LOGGER.setLevel(logging.INFO)


def create_package(
    job_id: int,
    job_name: str,
    description: str,
    router_name: str,
    provider: str,
    bbox: List[float],
    result_path: str,
    in_pbf_path: str,
    compression: str,
    user_email: str,
    config_string='production',
    cleanup=True
):
    """
    Creates a routing package and puts it in a defined folder.
    """

    # We need to create a new app for this, RQ runs async
    # and has no Flask context otherwise
    app = create_app(config_string)
    app_ctx = app.app_context()
    app_ctx.push()

    session: SessionBase = db.session

    # Set up the logger where we have access to the user email
    # and only if there hasn't been one before
    if not LOGGER.handlers:
        handler = AppSmtpHandler(**get_smtp_details(app.config, [user_email]))
        handler.setLevel(logging.INFO)
        LOGGER.addHandler(handler)

    bbox_geom: Polygon = bbox_to_geom(bbox)

    job = Job.query.get(job_id)
    succeeded = False

    # Huge try/except to make sure we only have to write a failure once.
    # Processing failures only raise HTTPErrors. If a job got deleted while it
    # was in the queue or even already running, any other exception will be thrown.
    # That way we can distinguish between the two scenarios and send emails accordingly.
    try:
        if not job:
            raise Exception(f"Job {job_id} doesn't exist anymore in the database.")
        job_status = job.status

        in_pbf_dir = app.config[provider.upper() + '_DIR']

        router = get_router(router_name, provider, in_pbf_path)

        # Set Redis job ID and container ID
        rq_job: Job = get_current_job()
        # testing has no access to a real queue
        if not app.testing:  # pragma: no cover
            job.set_rq_id(rq_job.id)
        job.set_container_id(router.container_id)

        # There's only 2 options how the PBF file is not available:
        # 1. The package just gets registered, so needs to be still extracted
        # 2. Smth went wrong in the pbf update or job deletion procedure
        if not os.path.isfile(in_pbf_path):
            # First take care of 2.
            if job_status == Statuses.COMPLETED.value:
                raise InternalServerError(
                    f"Job {job_id} couldn't find its corresponding PBF file {in_pbf_path}"
                )
            # Then take care of 1.
            try:
                best_pbf_path = get_pbfs_by_area(in_pbf_dir, bbox_geom)[0][0]
            # Raise a HTTP Error to not mess with error handling here
            except (AssertionError, FileNotFoundError) as e:
                raise InternalServerError(str(e))

            # Cut the PBF to the bbox extent (osmium availability is checked in __init__.py)
            osmium_proc = extract_proc(bbox_geom, best_pbf_path, in_pbf_path)

            job.set_status(Statuses.EXTRACTING.value)
            session.commit()

            # Let osmium cut the local PBF
            osmium_status = osmium_proc.wait()
            if osmium_status:  # pragma: no cover
                raise InternalServerError(f"'osmium': {osmium_proc.stderr.read().decode()}")

            # Check validity
            osmium_reader = Reader(in_pbf_path)
            if osmium_reader.header().box().bottom_left.lat == 0:
                raise InternalServerError(
                    f"'osmium': Apparently bbox {bbox} is not within the extent of {in_pbf_path}"
                )

        job.set_status(Statuses.TILING.value)
        session.commit()

        try:
            exit_code, output = router.build_graph()
            if exit_code:  # pragma: no cover
                raise InternalServerError(f"'{router.name()}': {output.decode()}")
        except ImageNotFound:
            raise InternalServerError(f"Docker image {router.image} not found.'")

        job.set_status(Statuses.COMPLETED.value)
        session.commit()

        succeeded = True
    # catch all exceptions we're actually aware of
    except HTTPException as e:
        job.set_status(Statuses.FAILED.value)
        session.commit()
        LOGGER.error(e.description, extra=dict(user=user_email, job_id=job_id))

        raise
    # any other exception is assumed to be a deleted job and will only be logged/email sent
    except Exception as e:  # pragma: no cover
        msg = f"Job {job_id} by {user_email} was deleted."
        LOGGER.warning(msg, extra=dict(user=user_email, job_id=job_id))
        raise
    finally:
        # always write the "last_ran" column
        job.set_last_finished(datetime.utcnow())
        session.commit()
        if not succeeded:
            shutil.rmtree(os.path.dirname(result_path))

        # Pop the context as we're done with app & db
        app_ctx.pop()

    # Write dataset to disk
    if compression == Compressions.ZIP.value:
        make_zipfile(result_path, router.graph_dir)
    elif compression == Compressions.TARGZ.value:
        make_tarfile(result_path, router.graph_dir)

    # Create the meta JSON
    fname = os.path.basename(result_path)
    j = {
        "job_id": job_id,
        "filepath": fname,
        "name": job_name,
        "description": description,
        "extent": ",".join([str(f) for f in bbox]),
        "last_modified": str(datetime.utcnow())
    }
    dirname = os.path.dirname(result_path)
    # Splits the first
    fname_sanitized = fname.split(os.extsep, 1)[0]
    with open(os.path.join(dirname, fname_sanitized + '.json'), 'w', encoding='utf8') as f:
        json.dump(j, f, indent=2, ensure_ascii=False)

    # only clean up if successful, otherwise retain the container for debugging
    if cleanup:
        router.cleanup()
    LOGGER.info(
        f"Job {job_id} by {user_email} finished successfully. Find the new dataset in {result_path}",
        extra={
            "job_id": job_id,
            "user": user_email
        }
    )

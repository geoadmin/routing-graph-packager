import os
import logging
from datetime import datetime
import json

from rq import get_current_job
from rq.job import Job
from flask_sqlalchemy import SessionBase
from werkzeug.exceptions import InternalServerError, HTTPException
from docker.errors import ImageNotFound
from shapely import wkb
from osmium.io import Reader

from . import create_app, db
from .api_v1.jobs.models import Job
from .utils.cmd_utils import osmium_extract_proc
from .logger import AppSmtpHandler, get_smtp_details
from .routers import get_router
from .utils.file_utils import make_tarfile, make_zipfile

LOGGER = logging.getLogger('packager')
LOGGER.setLevel(logging.INFO)


def create_package(
    router_name: str, job_id: str, user_email: str, config_string='production', cleanup=True
):
    """
    Creates a routing package and puts it in a defined folder.
    """

    # We need to create a new app for this, RQ runs async
    # and has no Flask context otherwise
    app = create_app(config_string)
    app_ctx = app.app_context()
    app_ctx.push()

    # Get the needed attributes
    job = Job.query.get(job_id)
    bbox = wkb.loads(bytes(job.bbox.data))
    provider = job.provider
    compression = job.compression
    result_path = job.path
    job_name = job.name
    description = job.description

    # Set up the paths
    in_pbf_path = app.config[provider.upper() + '_PBF_PATH']
    out_pbf_dir = app.config['TEMP_DIR']
    cut_pbf_path = os.path.join(out_pbf_dir, router_name, f'{router_name}_{provider}_cut.pbf')

    # Set up the logger where we have access to the user email
    # and only if there hasn't been one before
    if not LOGGER.handlers:
        handler = AppSmtpHandler(**get_smtp_details(app.config, [user_email]))
        handler.setLevel(logging.INFO)
        LOGGER.addHandler(handler)

    router = get_router(router_name, cut_pbf_path)
    session: SessionBase = db.session

    # Set Redis job ID and container ID
    rq_job: Job = get_current_job()
    # testing has no access to a real queue
    if not app.testing:  # pragma: no cover
        job.set_rq_id(rq_job.id)
    job.set_container_id(router.container_id)

    # Huge try/except to make sure we only have to write a failure once
    # Only raise HTTPErrors so we can distinguish a job deletion from a
    # processing failure.
    try:
        # Cut the PBF to the bbox extent (osmium availability is checked in __init__.py)
        osmium_proc = osmium_extract_proc(bbox, in_pbf_path, cut_pbf_path)

        # Also commit the other stuff from further up
        job.set_status('Extracting')
        session.commit()

        osmium_status = osmium_proc.wait()
        if osmium_status:  # pragma: no cover
            raise InternalServerError(f"'osmium': {osmium_proc.stderr.read().decode()}")

        # Check the cut PBF on validity
        osmium_reader = Reader(cut_pbf_path)
        if osmium_reader.header().box().bottom_left.lat == 0:
            raise InternalServerError(
                f"'osmium': Apparently bbox {bbox.bounds} is not within the extent of {in_pbf_path}"
            )
        try:
            job.set_status('Tiling')
            session.commit()

            exit_code, output = router.build_graph()
            if exit_code:  # pragma: no cover
                raise InternalServerError(f"'{router.name()}': {output.decode()}")
        except ImageNotFound:
            raise InternalServerError(f"Docker image {router.image} not found.'")

        job.set_status('Completed')
        session.commit()
    # catch all exceptions we're actually aware of
    except HTTPException as e:
        job.set_status('Failed')
        session.commit()
        LOGGER.error(e.description, extra=dict(router=router.name(), container_id=router.container_id))
        raise
    # any other exception is assumed to be a deleted job and will only be logged/email sent
    except Exception as e:  # pragma: no cover
        msg = f"Job {job_id} by {user_email} was deleted."
        LOGGER.warning(msg, extra=dict(user=user_email, job_id=job_id))

        raise
    finally:
        # always write the "last_ran" column
        job.set_last_ran(datetime.utcnow())
        session.commit()

        # Pop the context as we're done with app & db
        app_ctx.pop()

    # Write dataset to disk
    if compression == 'zip':
        make_zipfile(result_path, router.graph_dir)
    elif compression == 'tar.gz':
        make_tarfile(result_path, router.graph_dir)

    # Create the meta JSON
    fname = os.path.basename(result_path)
    j = {
        "job_id": job_id,
        "filepath": fname,
        "name": job_name,
        "description": description,
        "extent": ",".join([str(f) for f in bbox.bounds]),
        "last_modified": str(datetime.utcnow())
    }
    dirname = os.path.dirname(result_path)
    # Splits the first
    fname_sanitized = fname.split(os.extsep, 1)[0]
    with open(os.path.join(dirname, fname_sanitized + '.json'), 'w') as f:
        f.write(json.dumps(j, indent=2))

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

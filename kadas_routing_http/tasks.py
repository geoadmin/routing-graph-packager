import os
import logging

from flask_sqlalchemy import SessionBase
from werkzeug.exceptions import InternalServerError, HTTPException
from docker.errors import ImageNotFound

from . import create_app, db
from .api_v1.jobs.models import Job
from .cmd_utils import osmium_extract_proc
from .logger import AppSmtpHandler, get_smtp_details
from .core.routers import get_router

LOGGER = logging.getLogger('packager')
LOGGER.setLevel(logging.INFO)

# We need to create a new app for this, RQ runs async
# and has no Flask context otherwise
app = create_app()
app.app_context().push()


def create_package(router_name: str, job_id: str, user_email: str):
    """
    Creates a routing package and puts it in a defined folder.
    """
    in_pbf_path = app.config['PBF_PATH']
    out_pbf_dir = app.config['TEMP_DIR']
    cut_pbf_path = os.path.join(out_pbf_dir, router_name, f'{router_name}_cut.pbf')

    # Set up the logger where we have access to the user email
    if not LOGGER.handlers:
        handler = AppSmtpHandler(**get_smtp_details(app.config, [user_email], False))
        handler.setLevel(logging.INFO)
        LOGGER.addHandler(handler)

    router = get_router(router_name, cut_pbf_path)

    job = Job.query.get(job_id)
    bbox = job.bbox
    job.set_container_id(router.container_id)

    session: SessionBase = db.session

    # Huge try/except to make sure we only have to write a failure once
    try:
        # Cut the PBF to the bbox extent (osmium availability is checked in __init__.py)
        osmium_proc = osmium_extract_proc(bbox, in_pbf_path, cut_pbf_path)

        osmium_status = osmium_proc.wait()
        if osmium_status:
            raise InternalServerError(f"'osmium': {osmium_proc.stderr.read().decode()}")
        try:
            job.set_status('Processing')
            session.commit()

            exit_code, output = router.build_graph()
            if exit_code:
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

    # only clean up if successful, otherwise retain the container for debugging
    router.cleanup()
    LOGGER.info(f"Job {job.id} by {user_email} finished successfully.")
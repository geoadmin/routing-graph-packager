import logging
from typing import List

from fastapi import HTTPException
from requests import Session

from .config import SETTINGS
from .utils.db_utils import get_db
from .api_v1.models import User, Job
from .constants import Statuses
from .logger import AppSmtpHandler, get_smtp_details

LOGGER = logging.getLogger("packager")
LOGGER.setLevel(logging.INFO)


async def create_package(
    ctx,
    job_id: int,
    job_name: str,
    description: str,
    router_name: str,
    provider: str,
    bbox: List[float],
    result_path: str,
    compression: str,
    user_id: str,
    cleanup=True,
):

    session: Session = ctx["session"]

    # Set up the logger where we have access to the user email
    # and only if there hasn't been one before
    if not LOGGER.handlers:
        user_email = session.query(User).get(user_id)
        handler = AppSmtpHandler(**get_smtp_details([user_email]))
        handler.setLevel(logging.INFO)
        LOGGER.addHandler(handler)

    # bbox_geom: Polygon = bbox_to_geom(bbox)

    job = session.query(Job).get(job_id)
    job.status = Statuses.STARTED
    session.commit()

    try:
        # just use valhalla_build_extract to copy the tiles somewhere else
        print("A")
    except HTTPException:
        pass


async def startup(ctx):
    """
    Opens a session/connection to DB.
    """
    ctx["session"]: Session = get_db()


async def shutdown(ctx):
    """
    Closes the session.
    """
    ctx["session"].close()


class WorkerSettings:
    """
    Settings for the ARQ worker.
    """

    on_startup = startup
    on_shutdown = shutdown
    redis_settings = SETTINGS.REDIS_URL
    functions = [create_package]

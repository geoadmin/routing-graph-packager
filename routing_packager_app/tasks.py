import logging
from typing import List

from arq.connections import RedisSettings
from fastapi import HTTPException
from sqlmodel import Session

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
    user_id: int,
    cleanup: True,
):

    session: Session = ctx["session"]

    # Set up the logger where we have access to the user email
    # and only if there hasn't been one before
    user_email = session.query(User).get(user_id).email
    if not LOGGER.handlers:
        handler = AppSmtpHandler(**get_smtp_details([user_email]))
        handler.setLevel(logging.INFO)
        LOGGER.addHandler(handler)
    log_extra = {"user": user_email, "job_id": job_id}

    # bbox_geom: Polygon = bbox_to_geom(bbox)

    job = session.query(Job).get(job_id)
    job.status = Statuses.STARTED
    session.commit()

    try:
        # TODO: use similar logic as in valhalla_build_extract to copy the tiles somewhere else
        # TODO: gzipping is synchronous, maybe follow
        #   https://arq-docs.helpmanual.io/#synchronous-jobs
        LOGGER.critical("A", extra=log_extra)
    except HTTPException:
        pass


async def startup(ctx):
    """
    Opens a session/connection to DB.
    """
    ctx["session"]: Session = next(get_db())


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
    redis_settings = RedisSettings.from_dsn(SETTINGS.REDIS_URL)
    functions = [create_package]

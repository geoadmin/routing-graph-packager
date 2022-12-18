import json
import logging
import os
from datetime import datetime

from arq.connections import RedisSettings
from fastapi import HTTPException
from sqlmodel import Session

from .api_v1.dependencies import split_bbox
from .config import SETTINGS
from .utils.db_utils import get_db
from .api_v1.models import User, Job
from .constants import Statuses
from .logger import AppSmtpHandler, get_smtp_details
from .utils.file_utils import make_zip
from .utils.valhalla_utils import get_tiles_with_bbox

LOGGER = logging.getLogger("packager")
LOGGER.setLevel(logging.INFO)


async def create_package(
    ctx, job_id: int, job_name: str, description: str, bbox: str, result_path: str, user_id: int
):

    session: Session = ctx["session"]

    # Set up the logger where we have access to the user email
    # and only if there hasn't been one before
    user_email = session.query(User).get(user_id).email
    if not LOGGER.handlers:
        handler = AppSmtpHandler(**get_smtp_details([user_email]))
        handler.setLevel(logging.INFO)
        LOGGER.addHandler(handler)
    #    log_extra = {"user": user_email, "job_id": job_id}

    job = session.query(Job).get(job_id)
    job.status = Statuses.STARTED
    session.commit()

    try:
        # TODO: gzipping is synchronous, maybe follow
        #   https://arq-docs.helpmanual.io/#synchronous-jobs
        valhalla_tiles = sorted(SETTINGS.VALHALLA_DIR.rglob("*.gph"))
        if not valhalla_tiles:
            raise HTTPException(404, f"No Valhalla tiles in {SETTINGS.VALHALLA_DIR.resolve()}")

        # Gather Valhalla tile paths
        tile_paths = get_tiles_with_bbox(valhalla_tiles, split_bbox(bbox))
        if not tile_paths or valhalla_tiles:
            raise HTTPException(
                404, f"No Valhalla tiles in {SETTINGS.VALHALLA_DIR.resolve()} in bbox {bbox}"
            )

        # zip up the tiles
        make_zip(tile_paths, SETTINGS.VALHALLA_DIR, result_path)

        # Create the meta JSON
        fname = os.path.basename(result_path)
        j = {
            "job_id": job_id,
            "filepath": fname,
            "name": job_name,
            "description": description,
            "extent": ",".join([str(f) for f in bbox]),
            "last_modified": str(datetime.utcnow()),
        }
        dirname = os.path.dirname(result_path)
        fname_sanitized = fname.split(os.extsep, 1)[0]
        with open(os.path.join(dirname, fname_sanitized + ".json"), "w", encoding="utf8") as f:
            json.dump(j, f, indent=2, ensure_ascii=False)

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

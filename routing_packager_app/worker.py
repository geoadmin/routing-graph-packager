import json
import logging
import os
from datetime import datetime
from pathlib import Path

from arq.connections import RedisSettings
from fastapi import HTTPException
import requests
import shutil
from sqlmodel import Session
from starlette.status import HTTP_200_OK

from .api_v1.dependencies import split_bbox
from .config import SETTINGS
from .db import get_db
from .api_v1.models import User, Job
from .constants import Statuses
from .logger import AppSmtpHandler, get_smtp_details
from .utils.file_utils import make_zip
from .utils.valhalla_utils import get_tiles_with_bbox

LOGGER = logging.getLogger("packager")
LOGGER.setLevel(logging.INFO)


async def create_package(
    ctx, job_id: int, job_name: str, description: str, bbox: str, zip_path: str, user_id: int
):
    session: Session = next(get_db())

    # Set up the logger where we have access to the user email
    # and only if there hasn't been one before
    user_email = session.query(User).get(user_id).email
    if not LOGGER.handlers:
        handler = AppSmtpHandler(**get_smtp_details([user_email]))
        handler.setLevel(logging.INFO)
        LOGGER.addHandler(handler)
    log_extra = {"user": user_email, "job_id": job_id}

    job: Job = session.query(Job).get(job_id)
    job.status = Statuses.COMPRESSING
    session.commit()

    succeeded = False
    try:
        # TODO: gzipping is synchronous, maybe follow
        #   https://arq-docs.helpmanual.io/#synchronous-jobs

        # get the active Valhalla instance
        current_valhalla_dir_str = ""
        for port in (8002, 8003):
            status = requests.get(f"{SETTINGS.VALHALLA_SERVER_IP}:{port}/status").status_code
            if not status == HTTP_200_OK:
                continue
            current_valhalla_dir_str = SETTINGS.get_valhalla_path(port)
            break

        if not current_valhalla_dir_str:
            raise HTTPException(
                500, "No Valhalla service online, check the Valhalla server's docker logs."
            )

        current_valhalla_dir = Path(current_valhalla_dir_str).resolve()

        # TODO: maybe introduce a .lock file in the current valhalla dir, so the Valhalla server
        #   won't start building a new tile set while this job is running a compression
        #   That carries some risk as after the last one ran and until it can create a .lock file
        #   here with the next one, a bit of time passes. Not much really, but surely measurable.
        valhalla_tiles = sorted(current_valhalla_dir.rglob("*.gph"))
        if not valhalla_tiles:
            raise HTTPException(404, f"No Valhalla tiles in {current_valhalla_dir.resolve()}")

        # Gather Valhalla tile paths
        tile_paths = get_tiles_with_bbox(valhalla_tiles, split_bbox(bbox), current_valhalla_dir)
        if not tile_paths:
            raise HTTPException(404, f"No Valhalla tiles in bbox {bbox}")

        # zip up the tiles
        make_zip(tile_paths, current_valhalla_dir, zip_path)

        # Create the meta JSON
        fname = os.path.basename(zip_path)
        j = {
            "job_id": job_id,
            "filepath": fname,
            "name": job_name,
            "description": description,
            "extent": ",".join([str(f) for f in bbox]),
            "last_modified": str(datetime.utcnow()),
        }
        dirname = os.path.dirname(zip_path)
        fname_sanitized = fname.split(os.extsep, 1)[0]
        with open(os.path.join(dirname, fname_sanitized + ".json"), "w", encoding="utf8") as f:
            json.dump(j, f, indent=2, ensure_ascii=False)

        LOGGER.info(
            f"Job {job_id} by {user_email} finished successfully. Find the new dataset in {zip_path}",
            extra=log_extra,
        )
        succeeded = True
    # catch all exceptions we're controlling
    except HTTPException as e:
        raise e
    # any other exception is assumed to be a deleted job and will only be logged/email sent
    except Exception:  # pragma: no cover
        msg = f"Job {job_id} by {user_email} was deleted."
        LOGGER.critical(msg, extra=log_extra)
        raise
    finally:
        final_status = Statuses.COMPLETED
        if not succeeded:
            shutil.rmtree(os.path.dirname(zip_path))
            final_status = Statuses.FAILED

        # always write the "last_finished" column
        job.last_finished = datetime.utcnow()
        job.status = final_status
        session.commit()


class WorkerSettings:
    """
    Settings for the ARQ worker.
    """

    redis_settings = RedisSettings.from_dsn(SETTINGS.REDIS_URL)
    functions = [create_package]

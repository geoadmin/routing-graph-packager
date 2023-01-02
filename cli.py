import asyncio
import logging
import time
from argparse import ArgumentParser
from typing import List

from arq import ArqRedis, create_pool
from arq.jobs import ResultNotFound
from arq.connections import RedisSettings
from fastapi import HTTPException
from sqlmodel import select, Session

from routing_packager_app import SETTINGS
from routing_packager_app.db import get_db
from routing_packager_app.api_v1.models import Job, User
from routing_packager_app.logger import AppSmtpHandler, get_smtp_details
from routing_packager_app.utils.geom_utils import wkbe_to_bbox, wkbe_to_geom


JOB_TIMEOUT = 60 * 60  # one hour to compress a single graph

description = "Runs the worker to update the ZIP packages."
parser = ArgumentParser(description=description)

# set up the logger basics
LOGGER = logging.getLogger("packager")


def _sort_jobs(jobs_: List[Job]):
    for job in jobs_:
        job.area = wkbe_to_geom(job.bbox).area

    return sorted(jobs_, key=lambda x: x.area, reverse=True)


async def update_jobs(jobs_: List[Job], user_email_: str):
    pool: ArqRedis = await create_pool(RedisSettings.from_dsn(SETTINGS.REDIS_URL))
    success_count: int = 0
    start_time = time.time()

    # loop through all jobs "synchronously" by waiting for each job's result
    for job in jobs_:
        log_extra = {"user": user_email_, "job_id": job.id}
        async_job = await pool.enqueue_job(
            "create_package",
            job.id,
            job.arq_id,
            job.description,
            wkbe_to_bbox(job.bbox),
            job.zip_path,
            job.user_id,
            True
            # TODO: possibly we can't use the same ID, since arq won't process
            #   the same ID twice, which would be needed for updating every package
            # _job_id=job.arq_id,
        )
        # catch all possible exceptions and send emails
        try:
            await async_job.result(timeout=JOB_TIMEOUT, poll_delay=10)
        except ResultNotFound:
            LOGGER.critical(f"Updating job {job.name} timed out.", extra=log_extra)
        except HTTPException as e:
            LOGGER.critical(f"Updating job {job.name} failed with '{e.detail}'", extra=log_extra)
        except Exception as e:
            LOGGER.critical(f"Updating job {job.name} failed with '{e}'", extra=log_extra)

        success_count += 1

    total_time = (time.time() - start_time) / 60
    if success_count == len(jobs):
        LOGGER.info(f"Updated {success_count} packages in {total_time} minutes.")
    else:
        LOGGER.warning(f"Updated {success_count} of {len(jobs)} packages in {total_time} minutes.")


if __name__ == "__main__":
    args = parser.parse_args()

    session: Session = get_db()

    # Run the updates as software owner/admin
    user_email = session.query(select(User).where(User.email == SETTINGS.ADMIN_EMAIL)).first()
    if not LOGGER.handlers:
        handler = AppSmtpHandler(**get_smtp_details([user_email]))
        handler.setLevel(logging.INFO)
        LOGGER.addHandler(handler)

    jobs = _sort_jobs(session.exec(select(Job).where(Job.update is True)).all())
    asyncio.run(update_jobs(jobs, user_email))

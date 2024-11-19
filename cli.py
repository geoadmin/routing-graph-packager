import asyncio
from asyncio import TimeoutError
import logging
import sys
import time
from argparse import ArgumentParser
from typing import List

from arq import ArqRedis, create_pool
from arq.jobs import ResultNotFound
from arq.connections import RedisSettings
from fastapi import HTTPException
from sqlmodel import select

from routing_packager_app import SETTINGS
from routing_packager_app.db import get_db
from routing_packager_app.api_v1.models import Job, User
from routing_packager_app.logger import AppSmtpHandler, get_smtp_details, LOGGER
from routing_packager_app.utils.geom_utils import wkbe_to_geom, wkbe_to_str

JOB_TIMEOUT = 60 * 60  # one hour to compress a single graph

description = "Runs the worker to update the ZIP packages."
parser = ArgumentParser(description=description)


def _sort_jobs(jobs_: List[Job]):
    out = list()
    for job in jobs_:
        out.append((wkbe_to_geom(job.bbox).area, job))

    out = sorted(out, key=lambda x: x[0], reverse=True)
    return [x[1] for x in out]


async def update_jobs(jobs_: List[Job], user_email_: str):
    pool: ArqRedis = await create_pool(RedisSettings.from_dsn(SETTINGS.REDIS_URL))
    success_count: int = 0
    start_time = time.time()

    # loop through all jobs "synchronously" by waiting for each job's result
    for job in jobs_:
        print(f"Updating package {job.arq_id} as user {user_email_}", file=sys.stderr)
        log_extra = {"user": user_email_, "job_id": job.id}
        async_job = await pool.enqueue_job(
            "create_package",
            job.id,
            job.arq_id,
            job.description,
            wkbe_to_str(job.bbox),
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
            LOGGER.critical(f"Job {job.name} is missing from queue.", extra=log_extra)
        except TimeoutError:
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
    with next(get_db()) as session:
        # Run the updates as software owner/admin
        user_email = session.exec(select(User).where(User.email == SETTINGS.ADMIN_EMAIL)).first().email
        if not LOGGER.handlers:
            handler = AppSmtpHandler(**get_smtp_details([user_email]))
            handler.setLevel(logging.INFO)
            LOGGER.addHandler(handler)

        jobs = session.exec(select(Job).where(Job.update == True)).all()  # noqa: E712
        jobs = _sort_jobs(jobs)

        print(f"INFO: Updating {len(jobs)} packages with user {user_email}...", file=sys.stderr)

        asyncio.run(update_jobs(jobs, user_email))

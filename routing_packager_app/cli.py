from typing import List

import click
from shapely.ops import transform

from .api_v1 import Job
from .tasks import create_package
from .constants import INTERVALS, CONF_MAPPER
from .utils.geom_utils import wkbe_to_geom, WGS_TO_MOLLWEIDE


def _sort_jobs(jobs: List[Job]):
    for job in jobs:
        job.area = transform(WGS_TO_MOLLWEIDE, wkbe_to_geom(job.bbox)).area

    return sorted(jobs, key=lambda x: x.area, reverse=True)


def register(app):
    """
    Registers the flask command
    """
    @app.cli.command('update')
    @click.argument('interval', type=click.Choice(INTERVALS))
    # Only for testing
    @click.option(
        '--config',
        '-c',
        type=click.Choice(tuple(CONF_MAPPER.keys())),
        default='production',
        help='Internal option'
    )
    def update(interval, config):
        f"""Update routing packages according to INTERVALs, one of {INTERVALS}."""
        jobs = _sort_jobs(Job.query.filter_by(interval=interval).all())
        for job in jobs:
            print(f"Queueing job {job.id} by {job.users.email}.")
            # Todo: needs adaptation on arguments for create_package
            app.task_queue.enqueue(
                create_package, job.router, job.id, job.users.email, config_string=config
            )

    return update

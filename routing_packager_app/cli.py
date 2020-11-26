from typing import List

import click
from shapely.ops import transform

from .api_v1 import Job
from .tasks import create_package
from .constants import INTERVALS, Statuses, CONF_MAPPER
from .utils.geom_utils import wkbe_to_bbox, wkbe_to_geom, WGS_TO_MOLLWEIDE


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
    # Solely to set the right environment for testing
    @click.option(
        '--config',
        '-c',
        type=click.Choice(tuple(CONF_MAPPER.keys())),
        default='production',
        help='Internal option'
    )
    def update(interval, config):
        """Update routing packages according to INTERVALs, one of ["daily", "weekly", "monthly"]."""
        jobs = _sort_jobs(Job.query.filter_by(interval=interval, status=Statuses.COMPLETED.value).all())
        for job in jobs:
            app.task_queue.enqueue(
                create_package,
                job.id,
                job.name,
                job.description,
                job.router,
                job.provider,
                wkbe_to_bbox(job.bbox),
                job.path,
                job.pbf_path,
                job.compression,
                job.users.email,
                config_string=config
            )

    return update

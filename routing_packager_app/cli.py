import click

from .api_v1 import Job
from .tasks import create_package
from .constants import INTERVALS, CONF_MAPPER


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
        jobs = Job.query.filter_by(interval=interval).all()
        # TODO: start with the biggest job first
        for job in jobs:
            print(f"Queueing job {job.id} by {job.users.email}.")
            app.task_queue.enqueue(
                create_package, job.router, job.id, job.users.email, config_string=config
            )

    return update

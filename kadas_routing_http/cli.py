import logging
import click

from flask import Flask

from .api_v1 import Job
from .tasks import create_package
from .constants import INTERVALS


def register(app: Flask):
    @app.cli.command('update')
    @click.argument('interval')
    def update(interval):
        """Update routing packages according to INTERVALs, one of ['daily', 'weekly', 'monthly', 'yearly']."""
        if interval not in INTERVALS:
            raise click.exceptions.BadArgumentUsage(f"INTERVAL needs to be one of {INTERVALS}")
        jobs = Job.query.filter_by(schedule=interval).all()
        for job in jobs:
            create_package(job.router, job.id, job.user.email)

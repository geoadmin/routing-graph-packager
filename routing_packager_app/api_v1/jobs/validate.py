import re

from werkzeug.exceptions import BadRequest, Conflict
from flask import current_app

from . import JobFields
from .models import JobSql
from ...constants import INTERVALS, COMPRESSIONS, STATUSES


def validate_post(args):
    """
    Validates the POST request parameters.

    :param dict args: request parameters
    """

    # all args except Description must have a value
    for arg, value in args.items():
        if arg != JobFields.DESCRIPTION and not value:
            raise BadRequest(f"'{arg}' is required in request.")

    name = args[JobFields.NAME]

    # Make sure name has no arbitrary (unallowed) characters for the filesystem
    match = re.match("^[^*&%/]+$", name)
    if not match:
        raise BadRequest("'name' cannot have characters *, &, /, %.")

    # make sure no other combo of name & router & provider exists
    existing_combo: JobSql = JobSql.query.filter(
        JobSql.name == args[JobFields.NAME],
        JobSql.provider == args[JobFields.PROVIDER],
        JobSql.router == args[JobFields.ROUTER],
    ).first()
    if existing_combo:
        raise Conflict(
            f"Combination of 'name' & 'router' & 'provider' already exists with ID {existing_combo.id}"
        )

    _validate_common(args)


def validate_get(args):
    """
    Validates the GET request parameters.

    :param dict args: request parameters
    """
    status = args.get(JobFields.STATUS)
    if status and status not in STATUSES:
        raise BadRequest(f"'status' must be one of {STATUSES}")
    _validate_common(args)


def _validate_common(args):
    # Routers must be valid
    allowed_routers = current_app.config["ENABLED_ROUTERS"]
    router = args.get(JobFields.ROUTER)
    if router and router not in allowed_routers:
        raise BadRequest(f"'router' must be one of the 'ENABLED_ROUTERS': {allowed_routers}")

    allowed_providers = current_app.config["ENABLED_PROVIDERS"]
    provider = args.get(JobFields.PROVIDER)
    if provider and provider not in allowed_providers:
        raise BadRequest(f"'provider' must be one of 'ENABLED_PROVIDERS': {allowed_providers}.")

    # bbox must be 4 floats
    bbox = args.get(JobFields.BBOX)
    if bbox:
        bbox_split = bbox.split(",")
        if not len(bbox_split) == 4:
            raise BadRequest(
                "'bbox' needs to be a comma-delimited string in the format minx,miny,maxx,maxy."
            )
        # Raises if float(x) is not possible, e.g. there's a string in bbox_split
        try:
            list(map(float, bbox_split))
        except ValueError:
            raise BadRequest("All coordinates in 'bbox' need to be of type float.")

    # Intervals must be valid
    interval = args.get(JobFields.INTERVAL)
    if interval and interval not in INTERVALS:
        raise BadRequest(f"'interval' must be one of {INTERVALS}")

    # Compression format
    compression = args.get(JobFields.COMPRESSION)
    if compression and compression not in COMPRESSIONS:
        raise BadRequest(f"'compression' must be one of {COMPRESSIONS}")

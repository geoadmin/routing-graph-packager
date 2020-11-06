from werkzeug.exceptions import BadRequest
from flask import current_app

from . import JobFields
from ...constants import INTERVALS


def validate_post(args):
    """
    Validates the POST request parameters.

    :param dict args: request parameters

    :rtype: bool
    """

    # all args except Description must have a value
    for arg, value in args.items():
        if arg != JobFields.DESCRIPTION and not value:
            raise BadRequest(f"'{arg}' is required in request.")

    # bbox must be 4 floats
    bbox_split = args['bbox'].split(',')
    if not len(bbox_split) == 4:
        raise BadRequest(
            f"'bbox' needs to be a comma-delimited string in the format minx,miny,maxx,maxy."
        )
    if not all([float(x) for x in bbox_split]):
        raise BadRequest(f"All coordinates in 'bbox' need to be of type float.")

    # Intervals must be valid
    if args['interval'] not in INTERVALS:
        raise BadRequest(f"'interval' must be one of {INTERVALS}")

    # Routers must be valid
    allowed_routers = current_app.config['ENABLED_ROUTERS']
    if args['router'] not in allowed_routers:
        raise BadRequest(f"'router' must be one of the 'ENABLED_ROUTERS': {allowed_routers}")

    allowed_providers = current_app.config['ENABLED_PROVIDERS']
    if args['provider'] not in allowed_providers:
        raise BadRequest(f"'provider' must be one of 'ENABLED_PROVIDERS': {allowed_providers}.")

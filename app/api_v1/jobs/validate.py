from werkzeug.exceptions import NotFound, BadRequest

from . import JobFields


def validate_post(args):
    """
    Validates the POST request parameters.

    :param dict args: request parameters

    :rtype: bool
    """

    for arg, value in args.items():
        if arg != JobFields.DESCRIPTION and not value:
            raise BadRequest(f"'{arg}' is required in request.")

    bbox_split = args['bbox'].split(',')
    if not len(bbox_split) == 4:
        raise BadRequest(
            f"'bbox' needs to be a comma-delimited string in the format minx,miny,maxx,maxy."
        )
    if not all([float(x) for x in bbox_split]):
        raise BadRequest(f"All coordinates in 'bbox' need to be of type float.")

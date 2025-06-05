import re
from typing import Tuple, Optional

from fastapi import HTTPException
from starlette.status import HTTP_400_BAD_REQUEST


def split_bbox(bbox: Optional[str] = "") -> Tuple[float, float, float, float]:
    """Splits a bbox string into a list of four floats. Expects the format minx,miny,maxx,maxy."""
    error_msg = "'bbox' needs to be a comma-delimited string in the format minx,miny,maxx,maxy."
    if not bbox:
        raise HTTPException(HTTP_400_BAD_REQUEST, error_msg)

    try:
        split = tuple((float(x) for x in bbox.split(",")))
    except (ValueError, AttributeError):
        raise HTTPException(HTTP_400_BAD_REQUEST, error_msg)
    if not len(split) == 4:
        raise HTTPException(
            HTTP_400_BAD_REQUEST,
            error_msg
        )
    # validate bbox
    if (split[0] >= split[2] or split[0] < -180 or split[2] > 180) or (
        bbox[1] >= bbox[3] or split[1] < -90 or split[3] > 90
    ):
        raise HTTPException(HTTP_400_BAD_REQUEST, "'bbox' has an invalid geometry.")

    return split


def get_validated_name(name: str) -> str:
    """Validates the name doesn't contain stuff that's not valid in filesystems"""
    match = re.match("^[^*&%/]+$", name)
    if not match:
        raise HTTPException(
            HTTP_400_BAD_REQUEST, "'name' cannot be empty or have characters *, &, /, %."
        )

    return name.replace(" ", "_")


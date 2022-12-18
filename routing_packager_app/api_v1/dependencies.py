import re
from typing import List, Optional

from fastapi import HTTPException
from starlette.status import HTTP_400_BAD_REQUEST


def split_bbox(bbox: Optional[str] = "5.9559,45.818,10.4921,47.8084") -> Optional[List[float]]:
    """Splits a bbox string into a list of four floats. Expects the format minx,miny,maxx,maxy."""
    if not bbox:
        return None

    error_msg = "'bbox' needs to be a comma-delimited string in the format minx,miny,maxx,maxy."
    try:
        split = [float(x) for x in bbox.split(",")]
    except (ValueError, AttributeError):
        raise HTTPException(HTTP_400_BAD_REQUEST, error_msg)
    if not len(split) == 4:
        raise HTTPException(
            HTTP_400_BAD_REQUEST,
            "'bbox' needs to be a comma-delimited string in the format minx,miny,maxx,maxy.",
        )

    return split


def get_validated_name(name: str) -> str:
    """Validates the name doesn't contain stuff that's not valid in filesystems"""
    match = re.match("^[^*&%/]+$", name)
    if not match:
        raise HTTPException(
            HTTP_400_BAD_REQUEST, "'name' cannot be empty or have characters *, &, /, %."
        )

    return name.replace(" ", "_")


def get_validated_bbox(bbox_str: str) -> str:
    """Sanity checks the BBOX."""
    bbox = split_bbox(bbox_str)

    # validate bbox
    if (bbox[0] >= bbox[2] or bbox[0] < -180 or bbox[2] > 180) or (
        bbox[1] >= bbox[3] or bbox[1] < -90 or bbox[3] > 90
    ):
        raise HTTPException(HTTP_400_BAD_REQUEST, "'bbox' has an invalid geometry.")
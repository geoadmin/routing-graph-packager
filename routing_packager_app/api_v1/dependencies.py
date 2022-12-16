import re
from typing import List, Optional

from fastapi import HTTPException
from starlette.status import HTTP_400_BAD_REQUEST


def split_bbox(bbox_str: Optional[str] = "") -> Optional[List[float]]:
    """Splits a bbox string into a list of four floats. Expects the format minx,miny,maxx,maxy."""
    if not bbox_str:
        return None

    error_msg = "'bbox' needs to be a comma-delimited string in the format minx,miny,maxx,maxy."
    try:
        split = [float(x) for x in bbox_str.split(",")]
    except (ValueError, AttributeError):
        raise HTTPException(HTTP_400_BAD_REQUEST, error_msg)
    if not len(split) == 4:
        raise HTTPException(
            HTTP_400_BAD_REQUEST,
            "'bbox' needs to be a comma-delimited string in the format minx,miny,maxx,maxy.",
        )

    return split


def validate_name(name: str) -> str:
    """Validates the name doesn't contain stuff that's not valid in filesystems"""
    match = re.match("^[^*&%/]+$", name)
    if not match:
        raise HTTPException(
            HTTP_400_BAD_REQUEST, "'name' cannot be empty or have characters *, &, /, %."
        )

    return name.replace(" ", "_")

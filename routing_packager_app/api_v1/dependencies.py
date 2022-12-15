import re
from typing import List, Optional

from fastapi import HTTPException
from starlette.status import HTTP_400_BAD_REQUEST

from ..db import SessionLocal


def split_bbox(input_: str) -> Optional[List[float]]:
    if not input_:
        return None

    error_msg = "'bbox' needs to be a comma-delimited string in the format minx,miny,maxx,maxy."
    try:
        split = [float(x) for x in input_.split(",")]
    except (ValueError, AttributeError):
        raise HTTPException(
            HTTP_400_BAD_REQUEST,
            error_msg
        )
    if not len(split) == 4:
        raise HTTPException(
            HTTP_400_BAD_REQUEST,
            "'bbox' needs to be a comma-delimited string in the format minx,miny,maxx,maxy."
        )

    return split


def validate_name(name: str) -> str:
    match = re.match("^[^*&%/]+$", name)
    if not match:
        raise HTTPException(HTTP_400_BAD_REQUEST, "'name' cannot be empty or have characters *, &, /, %.")

    return name


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from fastapi.security import HTTPBasicCredentials
from sqlmodel import Session
from starlette.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
)

from ...auth.basic_auth import BasicAuth
from ...config import SETTINGS
from ...db import get_db
from ..models import LogType, User

router = APIRouter()


@router.get("/{log_type}", response_class=PlainTextResponse)
def get_logs(
    log_type: LogType,
    lines: int | None = None,
    db: Session = Depends(get_db),
    auth: HTTPBasicCredentials = Depends(BasicAuth),
):
    # first authenticate
    req_user = User.get_user(db, auth)
    if not req_user:
        raise HTTPException(HTTP_401_UNAUTHORIZED, "Not authorized to read logs.")

    # figure out the type of logs
    log_file = SETTINGS.get_logging_dir() / f"{log_type.value}.log"

    try:
        with open(log_file) as fh:
            if lines is None:
                return fh.read()
            line_count = len([1 for _ in fh.readlines()])
            start_i = line_count - lines if line_count > lines else 0
            response = ""
            fh.seek(0)
            for i, line in enumerate(fh.readlines()):
                if i < start_i:
                    continue
                response += line
            return response

    except:  # noqa
        return HTTP_400_BAD_REQUEST(f"Unable to open {log_file}.")

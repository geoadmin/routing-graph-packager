from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from fastapi.security import HTTPBasicCredentials
from sqlmodel import Session
from starlette.status import (
    HTTP_401_UNAUTHORIZED,
    HTTP_500_INTERNAL_SERVER_ERROR,
)

from ..auth import BasicAuth, HeaderKey
from ...config import SETTINGS
from ...db import get_db
from ..models import LogType, User, APIKeys, APIPermission

router = APIRouter()


@router.get("/{log_type}", response_class=PlainTextResponse)
def get_logs(
    log_type: LogType,
    lines: int | None = None,
    db: Session = Depends(get_db),
    auth: HTTPBasicCredentials = Depends(BasicAuth),
    key: str = Depends(HeaderKey),
):
    # check api key is valid and active
    matched_key = APIKeys.check_key(db, key, APIPermission.INTERNAL)

    # alternatively, allow basic auth
    current_user = User.get_user(db, auth)
    if not current_user and not matched_key:
        raise HTTPException(
            HTTP_401_UNAUTHORIZED,
            "No valid authentication method provided. Possible authentication methods: API key"
            "(x-api-key header) username/password (basic auth).",
        )

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
        return HTTPException(HTTP_500_INTERNAL_SERVER_ERROR, f"Unable to open {log_file}.")

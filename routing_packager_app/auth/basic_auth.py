import base64
from typing import Optional

from fastapi import HTTPException
from fastapi.security.base import SecurityBase
from fastapi.security.utils import get_authorization_scheme_param
from sqlalchemy.orm import Session
from starlette.requests import Request
from starlette.status import HTTP_403_FORBIDDEN


class BasicAuth(SecurityBase):
    async def __call__(self, request: Request) -> Optional[str]:
        authorization: str = request.headers.get("Authorization")
        scheme, param = get_authorization_scheme_param(authorization)
        if not authorization or scheme.lower() != "basic":
            raise HTTPException(
                status_code=HTTP_403_FORBIDDEN, detail="Not authenticated"
            )

        return param

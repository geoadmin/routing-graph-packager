from typing import List

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBasicCredentials
from sqlalchemy.orm import Session
from starlette.responses import Response
from starlette.status import HTTP_409_CONFLICT, HTTP_204_NO_CONTENT
from werkzeug.exceptions import Forbidden

from . import router
from ..dependencies import get_db
from ..models.users import UserResponse, UserSql
from ... import SETTINGS
from ...auth.basic_auth import BasicAuth


@router.post("/", response_model=UserResponse)
async def post_user(
    user_email: str,
    password: str,
    db: Session = Depends(get_db),
    auth: HTTPBasicCredentials = Depends(BasicAuth)
):
    """POST a new user. Needs admin privileges"""
    UserSql.get_user_id(auth)
    user = UserSql(user_email, password)
    db.add(user)
    db.commit()

    return user


@router.get("/", response_model=List[UserResponse])
async def get_users(db: Session = Depends(get_db),):
    """GET all users."""
    return db.query(UserSql).all()


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id, db: Session = Depends(get_db)):
    db.query(UserSql).get_or_404(user_id)


@router.delete("/{user_id}")
async def delete_user(user_id, db: Session = Depends(get_db), auth: HTTPBasicCredentials = Depends(BasicAuth)):
    req_user_id = UserSql.get_user_id(auth)
    req_user_email = db.query(UserSql).get(req_user_id).email

    user: UserSql = UserSql.query.get_or_404(user_id)
    if user.email == SETTINGS.ADMIN_EMAIL:
        raise HTTPException(HTTP_409_CONFLICT, "Can't delete admin user.")
    elif not req_user_email == SETTINGS.ADMIN_EMAIL:
        raise Forbidden("Admin privileges are required to delete a user.")

    db.delete(user)
    db.commit()
    return Response(HTTP_204_NO_CONTENT)

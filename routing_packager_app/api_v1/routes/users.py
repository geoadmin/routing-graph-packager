from typing import List

from fastapi import Depends, HTTPException, APIRouter
from fastapi.security import HTTPBasicCredentials
from sqlmodel import Session, select
from starlette.responses import Response
from starlette.status import (
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_404_NOT_FOUND,
    HTTP_409_CONFLICT,
)

from ..models import User, UserRead, UserCreate
from ...utils.db_utils import delete_or_abort, add_or_abort
from ...db import get_db
from ...config import SETTINGS
from ...auth.basic_auth import BasicAuth

router = APIRouter()


@router.post("/", response_model=UserRead)
def post_user(
    user: UserCreate, db: Session = Depends(get_db), auth: HTTPBasicCredentials = Depends(BasicAuth)
):
    """POST a new user. Needs admin privileges"""
    if not User.get_user(db, auth):
        raise HTTPException(HTTP_401_UNAUTHORIZED, "Wrong username or password.")

    user_db = User.from_orm(user)
    user_db.password = auth.password

    add_or_abort(db, user_db)

    return user_db


@router.get("/", response_model=List[UserRead])
def get_users(
    db: Session = Depends(get_db),
):
    """GET all users."""
    return db.exec(select(User)).all()


@router.get("/{user_id}", response_model=UserRead)
def get_user(user_id, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(HTTP_404_NOT_FOUND, f"Couldn't find user id {user_id}")

    return user


@router.delete("/{user_id}")
def delete_user(user_id, db: Session = Depends(get_db), auth: HTTPBasicCredentials = Depends(BasicAuth)):
    # first authenticate
    req_user = User.get_user(db, auth)
    if not req_user:
        raise HTTPException(HTTP_401_UNAUTHORIZED, "Not authorized to delete a user.")

    user: User = db.get(User, user_id)
    if not user:
        raise HTTPException(HTTP_404_NOT_FOUND, f"Couldn't find user id {user_id}")
    if user.email == SETTINGS.ADMIN_EMAIL:
        raise HTTPException(HTTP_409_CONFLICT, "Can't delete admin user.")
    elif not req_user.email == SETTINGS.ADMIN_EMAIL:
        raise HTTPException(HTTP_400_BAD_REQUEST, "Admin privileges are required to delete a user.")

    delete_or_abort(db, user)

    return Response("", HTTP_204_NO_CONTENT)

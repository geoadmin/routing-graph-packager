from fastapi import APIRouter

from . import jobs, users

api_v1_router = APIRouter()
api_v1_router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
api_v1_router.include_router(users.router, prefix="/users", tags=["users"])

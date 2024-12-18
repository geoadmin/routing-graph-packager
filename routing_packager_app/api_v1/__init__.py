from fastapi import APIRouter

from .routes import jobs, logs, users

api_v1_router = APIRouter()
api_v1_router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
api_v1_router.include_router(users.router, prefix="/users", tags=["users"])
api_v1_router.include_router(logs.router, prefix="/logs", tags=["logs"])

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware

from .api_v1 import api_v1_router
from .config import SETTINGS


def create_app():
    """
    Creates a FastAPI app dynamically.
    """

    with open(SETTINGS.DESCRIPTION_PATH) as fh:
        description = fh.read()

    app = FastAPI(title="Routing Graph Packager App", description=description)
    register_middlewares(app)
    register_router(app)

    return app


def register_router(app: FastAPI):
    app.include_router(api_v1_router, prefix="/api/v1")


def register_middlewares(app: FastAPI):
    # only from 1kb we'll do gzipping
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    if SETTINGS.CORS_ORIGINS:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=SETTINGS.CORS_ORIGINS,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

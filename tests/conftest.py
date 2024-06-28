from base64 import b64encode
import shutil

import pytest
from arq import Worker
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session

from routing_packager_app import create_app
from routing_packager_app.config import SETTINGS
from routing_packager_app.worker import create_package
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    pass


@pytest.fixture(scope="session", autouse=True)
def create_worker():
    """Auto-runs and creates an event loop for the worker."""
    worker = Worker([create_package])
    worker.async_run()
    yield
    worker.close()


@pytest.fixture(scope="session", autouse=False)
def get_app() -> FastAPI:
    app = create_app(lifespan=lifespan)

    return app


@pytest.fixture(scope="session")
def get_client(get_app: FastAPI) -> TestClient:
    client = TestClient(get_app)

    return client


@pytest.fixture(scope="session", autouse=True)
def create_db():
    from routing_packager_app.db import engine
    from routing_packager_app.api_v1.models import User

    SQLModel.metadata.create_all(engine, checkfirst=True)
    User.add_admin_user(Session(engine))
    yield
    SQLModel.metadata.drop_all(engine, checkfirst=True)


@pytest.fixture(scope="function")
def get_session():
    from routing_packager_app.db import engine

    db = Session(engine, autocommit=False, autoflush=False)
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session")
def basic_auth_header():
    admin_email = SETTINGS.ADMIN_EMAIL
    admin_pass = SETTINGS.ADMIN_PASS

    auth_encoded = b64encode(bytes(":".join((admin_email, admin_pass)).encode("utf-8"))).decode()
    auth_header = {"Authorization": f"Basic {auth_encoded}"}

    return auth_header


# Creates needed directories and removes them after the test function
@pytest.fixture(scope="session", autouse=True)
def handle_dirs():
    paths = [SETTINGS.get_valhalla_path(p) for p in (8002, 8003)]
    for p in paths:
        p.mkdir(parents=True, exist_ok=True)
    yield
    for p in paths:
        shutil.rmtree(p, ignore_errors=True)

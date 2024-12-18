import shutil
from base64 import b64encode
from contextlib import asynccontextmanager

import pytest
from arq import Worker
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel

from routing_packager_app import create_app
from routing_packager_app.config import SETTINGS
from routing_packager_app.worker import create_package


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
    from routing_packager_app.api_v1.models import User
    from routing_packager_app.db import engine

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
    paths.append(SETTINGS.get_logging_dir())
    for p in paths:
        p.mkdir(parents=True, exist_ok=True)
    yield
    for p in paths:
        shutil.rmtree(p, ignore_errors=True)

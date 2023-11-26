from shutil import rmtree, copytree

import pytest
from pytest_httpserver import HTTPServer
from sqlmodel import Session, select

from routing_packager_app import SETTINGS
from routing_packager_app.api_v1.models import Job


# alter the default port for the HTTP test server:
# https://pytest-httpserver.readthedocs.io/en/latest/howto.html#customizing-host-and-port
HTTPServer.DEFAULT_LISTEN_PORT = 8002
HTTPServer.DEFAULT_LISTEN_HOST = "localhost"


@pytest.fixture(scope="function", autouse=True)
def delete_jobs(get_session: Session):
    yield
    jobs = get_session.exec(select(Job)).all()
    for job in jobs:
        get_session.delete(job)
        get_session.commit()


@pytest.fixture(scope="function", autouse=True)
def delete_dirs():
    yield
    for dir_ in SETTINGS.get_output_path().iterdir():
        rmtree(dir_)


@pytest.fixture(scope="function")
def copy_valhalla_tiles():
    for dir_ in SETTINGS.get_output_path().parent.joinpath("andorra_tiles").iterdir():
        copytree(dir_, SETTINGS.get_valhalla_path(8002).joinpath(dir_.stem))
    yield
    rmtree(SETTINGS.get_valhalla_path(8002))

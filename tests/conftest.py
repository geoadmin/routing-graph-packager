import pytest
from flask import Flask

from app import create_app
from . import utils


@pytest.yield_fixture(scope='session')
def flask_app():
    app = create_app(config_string='testing')
    from app import db
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.yield_fixture(scope='session')
def db(flask_app: Flask):
    from app import db as db_instance
    yield db_instance


@pytest.fixture(scope='session')
def flask_app_client(flask_app: Flask):
    flask_app.response_class = utils.JSONResponse
    return flask_app.test_client()

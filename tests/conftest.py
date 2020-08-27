import pytest
from flask import Flask
from base64 import b64encode

from app import create_app
from . import utils


@pytest.yield_fixture(scope='session')
def flask_app():
    app = create_app(config_string='testing')
    from app import db
    with app.app_context():
        db.create_all()
        yield app
        db.session.close()
        db.drop_all()


@pytest.yield_fixture(scope='session')
def db():
    from app import db as db_instance
    yield db_instance


@pytest.fixture(scope='session')
def flask_app_client(flask_app: Flask):
    flask_app.response_class = utils.JSONResponse
    return flask_app.test_client()


@pytest.fixture(scope='session')
def basic_auth_header(flask_app: Flask):
    admin_email = flask_app.config['ADMIN_EMAIL']
    admin_pass = flask_app.config['ADMIN_PASS']

    auth_encoded = b64encode(bytes(':'.join((admin_email, admin_pass)).encode('utf-8'))).decode()
    auth_header = {'Authorization': f'Basic {auth_encoded}'}

    return auth_header

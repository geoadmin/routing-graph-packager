import pytest
from flask import Flask
from base64 import b64encode

from app import create_app
from app.db_utils import add_admin_user
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


# @pytest.yield_fixture(scope='function', autouse=True)
# def delete_tables(flask_app):
#     from app import db
#     with flask_app.app_context():
#         db.create_all()
#         add_admin_user()
#         yield
#         db.drop_all()


@pytest.yield_fixture(scope='session')
def db(flask_app: Flask):
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

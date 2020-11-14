from base64 import b64encode
import os
import shutil

import pytest
from flask import Flask
from flask.cli import ScriptInfo

from routing_packager_app import create_app
from routing_packager_app.api_v1 import Job
from routing_packager_app.utils.file_utils import make_directories
from . import utils


@pytest.yield_fixture(scope='function')
def delete_jobs():
    yield
    Job.query.delete()


@pytest.yield_fixture(scope='session')
def flask_app():
    app = create_app(config_string='testing')
    from routing_packager_app import db
    with app.app_context():
        db.create_all()
        yield app
        db.session.close()
        db.drop_all()


@pytest.yield_fixture(scope='session')
def db():
    from routing_packager_app import db as db_instance
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


# For testing cli
@pytest.fixture
def script_info(flask_app):
    return ScriptInfo(create_app=lambda info: flask_app)


@pytest.yield_fixture(scope='function')
def handle_dirs(flask_app):
    main_dir = flask_app.config['DATA_DIR']
    make_directories(
        main_dir,
        flask_app.config['TEMP_DIR'],
        flask_app.config['ENABLED_ROUTERS'],
    )
    yield
    for e in os.listdir(main_dir):
        p = os.path.join(main_dir, e)
        if os.path.isdir(p):
            shutil.rmtree(p, ignore_errors=True)

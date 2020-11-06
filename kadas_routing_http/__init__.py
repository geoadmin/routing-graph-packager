import os
from shutil import which
import logging

from flask import Flask, g
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import docker
from docker.errors import ImageNotFound, NullResource
from redis import Redis
from rq import Queue

log = logging.getLogger(__name__)

db = SQLAlchemy()
migrate = Migrate()

CONF_MAPPER = {
    'development': 'config.DevConfig',
    'production': 'config.ProdConfig',
    'testing': 'config.TestingConfig'
}


def create_app(config_string='production'):
    """Factory to create contextful apps."""
    app = Flask(__name__)

    config_env = os.getenv('FLASK_CONFIG')
    config_string = config_env or config_string

    # some quick sanity checks
    try:
        app.config.from_object(CONF_MAPPER[config_string])  # throws KeyError
        if not os.path.exists(app.config['PBF_PATH']):
            raise FileNotFoundError(f"PBF_PATH '{app.config['PBF_PATH']}' doesn't exist.")
        # Are all Docker images installed?
        enabled_routers = app.config['ENABLED_ROUTERS']
        docker_clnt = docker.from_env()
        for r in enabled_routers:
            env_var = f'{r.upper()}_IMAGE'
            docker_clnt.images.get(app.config.get(env_var))  # Throws ImageNotFound error
        # osmium is needed too
        if not which('osmium'):
            raise FileNotFoundError('"osmium" is not installed or not added to PATH.')
    except KeyError:
        log.error(
            f"'FLASK_CONFIG' needs to be one of testing, development, production. '{config_env}' is invalid."
        )
        raise
    except (NullResource, ImageNotFound, FileNotFoundError) as e:
        log.error(e)
        raise e

    # Flask complains about missing trailing slashes
    app.url_map.strict_slashes = False

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    app.redis = Redis.from_url(app.config['REDIS_URL'])
    app.task_queue = Queue(
        'packaging',
        connection=app.redis,
        job_timeout='5h'  # after 5 hours processing the job will be considered as failed
    )

    # Add a master account on first request
    @app.before_first_request
    def initialize_app():
        # TODO: remove once released, then migrate will take over this job
        if config_string == 'development':
            db.create_all()
        # Make sure g has db
        initialize_request()

        from kadas_routing_http.db_utils import add_admin_user
        add_admin_user()

    # Add the db to g to avoid circular imports
    @app.before_request
    def initialize_request():
        if not hasattr(g, 'db'):
            g.db = db

    # initialize the API module(s)
    # placed here to avoid circular imports
    from kadas_routing_http.api_v1 import (bp as api_v1, init_app as init_v1)

    init_v1(app)
    app.register_blueprint(api_v1)

    return app

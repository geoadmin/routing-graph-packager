import os
from shutil import which
import logging

from flask import Flask, g
from flask_sqlalchemy import SQLAlchemy
import docker
from docker.errors import ImageNotFound, NullResource
from redis import Redis
from rq import Queue

from .utils.file_utils import make_directories
from .constants import CONF_MAPPER

log = logging.getLogger(__name__)

db = SQLAlchemy()


def create_app(config_string="production"):
    """Factory to create contextful apps."""
    app = Flask(__name__)
    # Flask complains about missing trailing slashes
    app.url_map.strict_slashes = False

    config_env = os.getenv("FLASK_CONFIG")
    config_string = config_env or config_string

    # some quick sanity checks
    try:
        app.config.from_object(CONF_MAPPER[config_string])  # throws KeyError

        # Some runtime config variables for flask
        app.config["FLASK_CONFIG"] = config_string
        # FIXME: remember inside a container this references /app/data, not the env var!!!
        data_dir = app.config["DATA_DIR"]
        app.config["TEMP_DIR"] = temp_dir = os.path.join(data_dir, "temp")
        app.config["OSM_DIR"] = os.path.join(data_dir, "osm")
        app.config["TOMTOM_DIR"] = os.path.join(data_dir, "tomtom")
        app.config["HERE_DIR"] = os.path.join(data_dir, "here")
    except KeyError:
        raise KeyError(
            f"'FLASK_CONFIG' needs to be one of testing, development, production. '{config_env}' is invalid."
        )
    try:
        # do the PBFs exist?
        for provider in app.config["ENABLED_PROVIDERS"]:
            provider_dir = app.config[provider.upper() + "_DIR"]
            provider_pbfs = list()
            for fn in os.listdir(provider_dir):
                fp = os.path.join(provider_dir, fn)
                if os.path.isfile(fp) and fp.endswith(".pbf"):
                    provider_pbfs.append(fn)
            if len(provider_pbfs) == 0:
                raise FileNotFoundError(f"No PBFs for {provider} in {provider_dir}")
        # Are all Docker images installed?
        docker_clnt = docker.from_env()
        for r in app.config["ENABLED_ROUTERS"]:
            env_var = f"{r.upper()}_IMAGE"
            docker_clnt.images.get(app.config.get(env_var))  # Throws ImageNotFound error
        # osmium is needed too
        if not which("osmium"):
            raise FileNotFoundError('"osmium" is not installed or not added to PATH.')
    except (NullResource, ImageNotFound, FileNotFoundError) as e:
        log.error(e)
        raise e

    # create all dirs
    make_directories(data_dir, temp_dir, app.config["ENABLED_ROUTERS"])

    # Initialize extensions
    db.init_app(app)
    # Put Redis as an app attribute to reference easier in other modules
    app.redis = Redis.from_url(app.config["REDIS_URL"])
    app.task_queue = Queue(
        "packaging",
        connection=app.redis,
        default_timeout="12h",  # after 12 hours processing the job will be considered as failed
    )

    # Add a master account and all tables before first request
    @app.before_first_request
    def initialize_app():
        db.create_all()
        # Make sure g has db
        initialize_request()

        from routing_packager_app.utils.db_utils import add_admin_user

        add_admin_user()

    # Add the db to g to avoid circular imports
    @app.before_request
    def initialize_request():
        if not hasattr(g, "db"):
            g.db = db

    # initialize the API module(s)
    # placed here to avoid circular imports
    from routing_packager_app.api_v1 import bp as api_v1, init_app as init_v1

    init_v1(app)
    app.register_blueprint(api_v1)

    return app

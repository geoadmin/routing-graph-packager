import os
from flask import Flask, g
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()
migrate = Migrate()

CONF_MAPPER = {
    'development': 'config.DevConfig',
    'production': 'config.ProdConfig',
    'testing': 'config.TestingConfig'
}


def create_app(config_string=None):
    """Factory to create contextful apps."""
    app = Flask(__name__)

    config_string = config_string or os.getenv('FLASK_CONFIG')
    app.config.from_object(CONF_MAPPER[config_string])

    # Flask complains about missing trailing slashes
    app.url_map.strict_slashes = False

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # Add a master account on first request
    @app.before_first_request
    def intialize_app():
        if config_string == 'development':
            db.create_all()
        # Make sure g has db
        initialize_request()

        from app.db_utils import add_admin_user
        add_admin_user()

    # Add the db to g to avoid circular imports
    @app.before_request
    def initialize_request():
        if not hasattr(g, 'db'):
            g.db = db

    # initialize the API module(s)
    # placed here to avoid circular imports
    from app.api_v1 import (bp as api_v1, init_app as init_v1)

    init_v1(app)
    app.register_blueprint(api_v1)

    return app

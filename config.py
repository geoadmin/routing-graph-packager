import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))


class BaseConfig(object):
    # Secrets
    SECRET_KEY = os.getenv(
        'SECRET_KEY'
    ) or '<MMs8?u_;rTt>;LarIGI&FjWhKNSe=%3|W;=DFDqOdx+~-rBS+K=p8#t#9E+;{e$'

    ADMIN_EMAIL = os.getenv('DB_ADMIN_EMAIL') or 'admin@example.org'
    ADMIN_PASS = os.getenv('DB_ADMIN_PASSWORD') or 'admin'

    # Flask
    SQLALCHEMY_DATABASE_URI = os.environ.get('SQLITE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    ERROR_INCLUDE_MESSAGE = False  # No default "message" field in error responses

    # Modules are the package names in app/api_vX
    ENABLED_MODULES = ['users']


class DevConfig(BaseConfig):
    SQLALCHEMY_DATABASE_URI = os.environ.get('SQLITE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app_dev.db')


class ProdConfig(BaseConfig):
    pass


class TestingConfig(BaseConfig):
    TESTING = True

    # Use in-memory database for testing
    SQLALCHEMY_DATABASE_URI = 'sqlite://'

    ADMIN_EMAIL = 'admin@example.org'
    ADMIN_PASS = 'admin'

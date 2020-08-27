import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))


def _get_list_var(var):
    out = []
    if var:
        out.extend(var.split(','))

    return out


class BaseConfig(object):
    # Secrets
    SECRET_KEY = os.getenv(
        'SECRET_KEY'
    ) or '<MMs8?u_;rTt>;LarIGI&FjWhKNSe=%3|W;=DFDqOdx+~-rBS+K=p8#t#9E+;{e$'

    ADMIN_EMAIL = os.getenv('DB_ADMIN_EMAIL') or 'admin@example.org'
    ADMIN_PASS = os.getenv('DB_ADMIN_PASSWORD') or 'admin'

    # Flask
    ERROR_INCLUDE_MESSAGE = False  # No default "message" field in error responses
    RESTX_MASK_SWAGGER = False  # No default MASK header in Swagger

    # DB
    POSTGRES_HOST = os.getenv('POSTGRES_HOST') or 'localhost'
    POSTGRES_PORT = os.getenv('POSTGRES_PORT') or '5432'
    POSTGRES_DB = os.getenv('POSTGRES_DB') or 'gis'
    POSTGRES_USER = os.getenv('POSTGRES_USER') or 'admin'
    POSTGRES_PASS = os.getenv('POSTGRES_PASS') or 'admin'
    SQLALCHEMY_DATABASE_URI = os.getenv('POSTGRES_URL') or \
        f'postgresql://{POSTGRES_USER}:{POSTGRES_PASS}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}'

    # SMTP
    SMTP_HOST = os.getenv('SMTP_HOST') or 'localhost'
    SMTP_PORT = os.getenv('SMTP_PORT') or '587'
    SMTP_FROM = os.getenv('SMTP_FROM') or 'example@kadas.org'
    SMTP_USER = os.getenv('SMTP_USER')
    SMTP_PASS = os.getenv('SMTP_PASS')
    SMTP_SECURE = os.getenv('SMTP_SECURE') or False

    # Routers & PBF
    PBF_PATH = os.getenv('PBF_PATH') or os.path.join(basedir, 'data', 'planet-latest.pbf')
    GRAPH_DIR = os.getenv('GRAPH_DIR') or os.path.join(basedir, 'data', 'graphs')
    os.makedirs(GRAPH_DIR, exist_ok=True)
    PBF_TEMP_DIR = os.getenv('PBF_TEMP_DIR') or os.path.join(basedir, 'data', 'temp')
    os.makedirs(PBF_TEMP_DIR, exist_ok=True)

    ENABLED_PROVIDERS = _get_list_var(os.getenv('ENABLED_PROVIDERS')) or ['osm']
    ENABLED_ROUTERS = _get_list_var(os.getenv('ENABLED_ROUTERS')) or ['valhalla']
    VALHALLA_IMAGE = os.getenv('VALHALLA_IMAGE') or 'gisops/valhalla:3.0.9'


class DevConfig(BaseConfig):
    pass


class ProdConfig(BaseConfig):
    pass


class TestingConfig(BaseConfig):
    TESTING = True

    POSTGRES_HOST = os.getenv('POSTGRES_HOST') or 'localhost'
    POSTGRES_PORT = os.getenv('POSTGRES_PORT') or '5432'
    POSTGRES_DB_TEST = 'gis_test'
    POSTGRES_USER = os.getenv('POSTGRES_USER') or 'admin'
    POSTGRES_PASS = os.getenv('POSTGRES_PASS') or 'admin'

    SQLALCHEMY_DATABASE_URI = os.getenv('POSTGRES_URL') or \
        f'postgresql://{POSTGRES_USER}:{POSTGRES_PASS}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB_TEST}'

    PBF_PATH = os.path.join(basedir, 'tests', 'data', 'andorra-200827.osm.pbf')

    ADMIN_EMAIL = 'admin@example.org'
    ADMIN_PASS = 'admin'

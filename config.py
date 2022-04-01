import os
from dotenv import load_dotenv
from distutils.util import strtobool

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, ".env"))


def _get_list_var(var):
    out = []
    if var:
        out.extend(var.split(","))

    return out


class BaseConfig(object):
    ### FLASK ###
    SECRET_KEY = (
        os.getenv("SECRET_KEY") or "<MMs8?u_;rTt>;LarIGI&FjWhKNSe=%3|W;=DFDqOdx+~-rBS+K=p8#t#9E+;{e$"
    )
    ERROR_INCLUDE_MESSAGE = False  # No default "message" field in error responses
    RESTX_MASK_SWAGGER = False  # No default MASK header in Swagger
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    ### APP ###
    ADMIN_EMAIL = os.getenv("ADMIN_EMAIL") or "admin@example.org"
    ADMIN_PASS = os.getenv("ADMIN_PASSWORD") or "admin"

    DATA_DIR = os.getenv("DATA_DIR") or os.path.join(basedir, "data")
    # if we're inside a docker container, we need to reference the fixed directory instead
    # Watch out for CI, also runs within docker
    if os.path.isdir("/app/data") and not os.getenv("CI", None):
        DATA_DIR = "/app/data"

    ENABLED_PROVIDERS = _get_list_var(os.getenv("ENABLED_PROVIDERS")) or ["osm"]
    ENABLED_ROUTERS = _get_list_var(os.getenv("ENABLED_ROUTERS")) or ["valhalla"]
    VALHALLA_IMAGE = os.getenv("VALHALLA_IMAGE") or "gisops/valhalla:latest"
    OSRM_IMAGE = os.getenv("OSRM_IMAGE") or "osrm/osrm-backend:latest"
    ORS_IMAGE = os.getenv("ORS_IMAGE") or "openrouteservice/openrouteservice:latest"
    GRAPHHOPPER_IMAGE = os.getenv("GRAPHHOPPER_IMAGE") or "graphhopper/graphhopper:latest"

    ### DATABASES ###
    POSTGRES_HOST = os.getenv("POSTGRES_HOST") or "localhost"
    POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", int())) or 5432
    POSTGRES_DB = os.getenv("POSTGRES_DB") or "gis"
    POSTGRES_USER = os.getenv("POSTGRES_USER") or "docker"
    POSTGRES_PASS = os.getenv("POSTGRES_PASS") or "docker"
    SQLALCHEMY_DATABASE_URI = (
        os.getenv("POSTGRES_URL")
        or f"postgresql://{POSTGRES_USER}:{POSTGRES_PASS}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    )
    REDIS_URL = os.getenv("REDIS_URL") or "redis://localhost:6379/0"

    ### SMTP ###
    SMTP_HOST = os.getenv("SMTP_HOST") or "localhost"
    SMTP_PORT = int(os.getenv("SMTP_PORT", int())) or 1025
    SMTP_FROM = os.getenv("SMTP_FROM") or "valhalla@kadas.org"
    SMTP_USER = os.getenv("SMTP_USER")
    SMTP_PASS = os.getenv("SMTP_PASS")
    SMTP_SECURE = bool(strtobool(os.getenv("SMTP_SECURE", "False"))) or False


class DevConfig(BaseConfig):
    pass


class ProdConfig(BaseConfig):
    pass


class TestingConfig(BaseConfig):
    TESTING = True
    FLASK_DEBUG = 0

    POSTGRES_HOST = os.getenv("POSTGRES_HOST") or "localhost"
    POSTGRES_PORT = os.getenv("POSTGRES_PORT") or "5432"
    POSTGRES_DB_TEST = os.getenv("POSTGRES_DB_TEST") or "gis_test"
    POSTGRES_USER = os.getenv("POSTGRES_USER") or "admin"
    POSTGRES_PASS = os.getenv("POSTGRES_PASS") or "admin"

    SQLALCHEMY_DATABASE_URI = (
        os.getenv("POSTGRES_TEST_URL")
        or f"postgresql://{POSTGRES_USER}:{POSTGRES_PASS}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB_TEST}"
    )

    DATA_DIR = os.path.join(basedir, "tests", "data")
    OSM_PBF_PATH = os.path.join(basedir, "tests", "data", "andorra-200827.osm.pbf")
    TOMTOM_PBF_PATH = os.path.join(basedir, "tests", "data", "liechtenstein-201109.tomtom.pbf")
    HERE_PBF_PATH = os.path.join(basedir, "tests", "data", "liechtenstein-201109.here.pbf")

    ENABLED_ROUTERS = _get_list_var("valhalla")
    ENABLED_PROVIDERS = _get_list_var("osm,tomtom,here")

    ADMIN_EMAIL = "admin@example.org"
    ADMIN_PASS = "admin"

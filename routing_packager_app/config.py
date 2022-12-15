import os
from pathlib import Path
from typing import List

from pydantic import BaseSettings as _BaseSettings

BASE_DIR = Path(__file__).parent.parent.resolve()
ENV_FILE = BASE_DIR.joinpath(".env")


def _get_list_var(var):
    out = []
    if var:
        out.extend(var.split(","))

    return out


class BaseSettings(_BaseSettings):
    SECRET_KEY: str = "<MMs8?u_;rTt>;LarIGI&FjWhKNSe=%3|W;=DFDqOdx+~-rBS+K=p8#t#9E+;{e$"
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False

    DESCRIPTION_PATH: Path = BASE_DIR.joinpath("DESCRIPTION.md")

    ### APP ###
    ADMIN_EMAIL: str = "admin@example.org"
    ADMIN_PASS: str = "admin"
    # TODO: clarify if there's a need to restrict origins
    CORS_ORIGINS: List[str] = ["http://localhost:5000", "http://localhost"]

    DATA_DIR: Path = os.path.join(BASE_DIR, "data")
    # if we're inside a docker container, we need to reference the fixed directory instead
    # Watch out for CI, also runs within docker
    if os.path.isdir("/app/data") and not os.getenv("CI", None):
        DATA_DIR = "/app/data"

    ENABLED_PROVIDERS: list[str] = ["osm"]
    ENABLED_ROUTERS: list[str] = ["valhalla"]
    VALHALLA_IMAGE: str = "gisops/valhalla:latest"
    OSRM_IMAGE: str = "osrm/osrm-backend:latest"
    ORS_IMAGE: str = "openrouteservice/openrouteservice:latest"
    GRAPHHOPPER_IMAGE: str = "graphhopper/graphhopper:latest"

    ### DATABASES ###
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "gis"
    POSTGRES_USER: str = "docker"
    POSTGRES_PASS: str = "docker"
    SQLALCHEMY_DATABASE_URI: str = (
        f"postgresql://{POSTGRES_USER}:{POSTGRES_PASS}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    )
    REDIS_URL: str = "redis://localhost:6379/0"

    ### SMTP ###
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 1025
    SMTP_FROM: str = "valhalla@kadas.org"
    SMTP_USER: str = "user"
    SMTP_PASS: str = "pass"
    SMTP_SECURE: bool = False

    class Config:
        case_sensitive = True
        env_file = ENV_FILE


class ProdSettings(BaseSettings):
    DEBUG: bool = False


class DevSettings(BaseSettings):
    DEBUG: bool = True


class TestSettings(BaseSettings):
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

    DATA_DIR = os.path.join(BASE_DIR, "tests", "data")

    ENABLED_ROUTERS = _get_list_var("valhalla")
    ENABLED_PROVIDERS = _get_list_var("osm,tomtom,here")

    ADMIN_EMAIL = "admin@example.org"
    ADMIN_PASS = "admin"


SETTINGS = DevSettings()

if not __debug__:
    SETTINGS = ProdSettings()

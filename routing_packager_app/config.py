import os
from pathlib import Path
from typing import List

from pydantic import BaseSettings as _BaseSettings
from starlette.datastructures import CommaSeparatedStrings

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

    DATA_DIR: Path = BASE_DIR.joinpath("data")
    # if we're inside a docker container, we need to reference the fixed directory instead
    # Watch out for CI, also runs within docker
    if os.path.isdir("/app/data") and not os.getenv("CI", None):
        DATA_DIR = "/app/data"

    ENABLED_PROVIDERS: list[str] = list(CommaSeparatedStrings("osm"))
    ENABLED_ROUTERS: list[str] = list(CommaSeparatedStrings("valhalla"))
    VALHALLA_IMAGE: str = "gisops/valhalla:latest"
    OSRM_IMAGE: str = "osrm/osrm-backend:latest"
    ORS_IMAGE: str = "openrouteservice/openrouteservice:latest"
    GRAPHHOPPER_IMAGE: str = "graphhopper/graphhopper:latest"

    ### DATABASES ###
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "gis_test"
    POSTGRES_USER: str = "nilsnolde"
    POSTGRES_PASS: str = "Manchmal88"
    SQLALCHEMY_DATABASE_URI: str = (
        f"postgresql://{POSTGRES_USER}:{POSTGRES_PASS}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    )
    REDIS_URL: str = "redis://localhost"

    ### SMTP ###
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 1025
    SMTP_FROM: str = "valhalla@kadas.org"
    SMTP_USER: str = ""
    SMTP_PASS: str = ""
    SMTP_SECURE: bool = False

    class Config:
        case_sensitive = True
        env_file = ENV_FILE


class ProdSettings(BaseSettings):
    DEBUG: bool = False

    class Config:
        case_sensitive = True
        env_file = ENV_FILE


class DevSettings(BaseSettings):
    DEBUG: bool = True

    class Config:
        case_sensitive = True
        env_file = ENV_FILE


class TestSettings(BaseSettings):
    TESTING = True
    FLASK_DEBUG = 0

    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB_TEST: str = "gis_test"
    POSTGRES_USER: str = "admin"
    POSTGRES_PASS: str = "admin"

    SQLALCHEMY_DATABASE_URI: str = (
        os.getenv("POSTGRES_TEST_URL")
        or f"postgresql://{POSTGRES_USER}:{POSTGRES_PASS}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB_TEST}"
    )

    DATA_DIR: Path = BASE_DIR.joinpath("tests", "data")

    ENABLED_ROUTERS: List[str] = CommaSeparatedStrings("valhalla")
    ENABLED_PROVIDERS: List[str] = CommaSeparatedStrings("osm,tomtom,here")

    ADMIN_EMAIL: str = "admin@example.org"
    ADMIN_PASS: str = "admin"


SETTINGS = DevSettings()

if not __debug__:
    SETTINGS = ProdSettings()

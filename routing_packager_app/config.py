import os
import sys
from pathlib import Path
from typing import List, Optional

from pydantic import BaseSettings as _BaseSettings
from starlette.datastructures import CommaSeparatedStrings

BASE_DIR = Path(__file__).parent.parent.resolve()
ENV_FILE = BASE_DIR.joinpath(".env")


class BaseSettings(_BaseSettings):
    SECRET_KEY: str = "<MMs8?u_;rTt>;LarIGI&FjWhKNSe=%3|W;=DFDqOdx+~-rBS+K=p8#t#9E+;{e$"
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False

    DESCRIPTION_PATH: Path = BASE_DIR.joinpath("DESCRIPTION.md")

    ### APP ###
    ADMIN_EMAIL: str = "admin@example.org"
    ADMIN_PASS: str = "admin"
    # TODO: clarify if there's a need to restrict origins
    CORS_ORIGINS: List[str] = ["http://localhost:5000", "http://localhost"]

    DATA_DIR: Path = BASE_DIR.joinpath("data/output")
    VALHALLA_SERVER_IP: str = "http://localhost"
    VALHALLA_DIR_8002: Path = str(BASE_DIR.joinpath("data/valhalla_tiles_8002"))
    VALHALLA_DIR_8003: Path = str(BASE_DIR.joinpath("data/valhalla_tiles_8003"))
    # if we're inside a docker container, we need to reference the fixed directory instead
    # Watch out for CI, also runs within docker
    if os.path.isdir("/app/data") and not os.getenv("CI", None):  # pragma: no cover
        DATA_DIR = "/app/data"

    ENABLED_PROVIDERS: list[str] = list(CommaSeparatedStrings("osm"))

    ### DATABASES ###
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "gis"
    POSTGRES_USER: str = "admin"
    POSTGRES_PASS: str = "admin"
    REDIS_URL: str = "redis://localhost"

    ### SMTP ###
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 1025
    SMTP_FROM: str = "valhalla@kadas.org"
    SMTP_USER: str = ""
    SMTP_PASS: str = ""
    SMTP_SECURE: bool = False

    def get_valhalla_path(self, port: int) -> Path:  # pragma: no cover
        if port == 8002:
            return self.VALHALLA_DIR_8002
        elif port == 8003:
            return self.VALHALLA_DIR_8003
        else:
            raise ""


class ProdSettings(BaseSettings):
    class Config:
        case_sensitive = True
        env_file = ENV_FILE


class DevSettings(BaseSettings):
    class Config:
        case_sensitive = True
        env_file = ENV_FILE


class TestSettings(BaseSettings):
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "gis_test"
    POSTGRES_DB_TEST: str = "gis_test"
    POSTGRES_USER: str = "admin"
    POSTGRES_PASS: str = "admin"

    DATA_DIR: Path = BASE_DIR.joinpath("tests", "data")

    ADMIN_EMAIL: str = "admin@example.org"
    ADMIN_PASS: str = "admin"

    class Config:
        case_sensitive = True
        env_file = BASE_DIR.joinpath("tests", "env")


# decide which settings we'll use
SETTINGS: Optional[BaseSettings] = None
env = os.getenv("API_CONFIG", "prod")
if env == "prod":  # pragma: no cover
    SETTINGS = ProdSettings()
elif env == "dev":  # pragma: no cover
    SETTINGS = DevSettings()
elif env == "test":
    SETTINGS = TestSettings()
else:  # pragma: no cover
    print("No valid 'API_CONFIG' environment variable, one of 'prod', 'dev' or 'test'")
    sys.exit(1)

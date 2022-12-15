from enum import Enum


class Routers(str, Enum):
    VALHALLA = "valhalla"
    ORS = "ors"
    OSRM = "osrm"
    GRAPHHOPPER = "graphhopper"


class Providers(str, Enum):
    OSM = "osm"
    TOMTOM = "tomtom"
    HERE = "here"


class Statuses(str, Enum):
    QUEUED = "Queued"
    STARTED = "Started"
    EXTRACTING = "Extracting"
    TILING = "Tiling"
    FAILED = "Failed"
    DELETED = "Deleted"
    COMPLETED = "Completed"


class Compressions(str, Enum):
    ZIP = "zip"
    TAR = "tar"


ROUTERS = [e.value for e in Routers]

PROVIDERS = [e.value for e in Providers]

STATUSES = [e.value for e in Statuses]

INTERVALS = [e.value for e in Intervals]

COMPRESSIONS = [e.value for e in Compressions]

CONF_MAPPER = {
    "development": "config.DevConfig",
    "production": "config.ProdConfig",
    "testing": "config.TestingConfig",
}

DOCKER_VOLUME = "routing-packager_packages"

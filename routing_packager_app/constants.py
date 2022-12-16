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


DOCKER_VOLUME = "routing-packager_packages"

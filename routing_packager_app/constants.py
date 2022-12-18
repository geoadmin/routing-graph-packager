from enum import Enum


class Providers(str, Enum):
    OSM = "osm"
    TOMTOM = "tomtom"
    HERE = "here"


class Statuses(str, Enum):
    QUEUED = "Queued"
    STARTED = "Started"
    PROCESSING = "Processing"
    FAILED = "Failed"
    DELETED = "Deleted"
    COMPLETED = "Completed"

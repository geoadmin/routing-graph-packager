from enum import Enum


class Routers(Enum):
    VALHALLA = 'valhalla'
    ORS = 'ors'
    OSRM = 'osrm'


class Providers(Enum):
    OSM = 'osm'
    TOMTOM = 'tomtom'
    HERE = 'here'


STATUSES = ['Starting', 'Processing', 'Failed', 'Deleted', 'Completed']

INTERVALS = ['once', 'daily', 'weekly', 'monthly', 'yearly']

COMPRESSIONS = ['zip', 'tar']
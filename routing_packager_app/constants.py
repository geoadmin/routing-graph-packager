from enum import Enum


class Routers(Enum):
    VALHALLA = 'valhalla'
    ORS = 'ors'
    OSRM = 'osrm'
    GRAPHHOPPER = 'graphhopper'


class Providers(Enum):
    OSM = 'osm'
    TOMTOM = 'tomtom'
    HERE = 'here'


ROUTERS = [e.value for e in Routers]

PROVIDERS = [e.value for e in Providers]

STATUSES = ['Queued', 'Extracting', 'Tiling', 'Failed', 'Deleted', 'Completed']

INTERVALS = ['once', 'daily', 'weekly', 'monthly']

COMPRESSIONS = ['zip', 'tar.gz']

CONF_MAPPER = {
    'development': 'config.DevConfig',
    'production': 'config.ProdConfig',
    'testing': 'config.TestingConfig'
}

DOCKER_VOLUME = 'routing-packager_packages'

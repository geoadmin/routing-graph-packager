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


class Statuses(Enum):
    QUEUED = 'Queued'
    EXTRACTING = 'Extracting'
    TILING = 'Tiling'
    FAILED = 'Failed'
    DELETED = 'Deleted'
    COMPLETED = 'Completed'


class Intervals(Enum):
    ONCE = 'once'
    DAILY = 'daily'
    WEEKLY = 'weekly'
    MONTHLY = 'monthly'


class Compressions(Enum):
    ZIP = 'zip'
    TARGZ = 'tar.gz'


ROUTERS = [e.value for e in Routers]

PROVIDERS = [e.value for e in Providers]

STATUSES = [e.value for e in Statuses]

INTERVALS = [e.value for e in Intervals]

COMPRESSIONS = [e.value for e in Compressions]

CONF_MAPPER = {
    'development': 'config.DevConfig',
    'production': 'config.ProdConfig',
    'testing': 'config.TestingConfig'
}

DOCKER_VOLUME = 'routing-packager_packages'

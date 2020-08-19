from flask import Blueprint
from flask_restx import Api

from .__version__ import __version__, __api_suffix__

bp = Blueprint(f'api_{__api_suffix__}', __name__, url_prefix=f'/api/{__api_suffix__}')

api = Api(
    bp,
    version=__version__,
    title='KADAS Routing Tile Generator',
    description=(
        """App to generate Valhalla routing tiles, including:
- email notification on final job status
- automatic placement on a hard disk, e.g. FTP
- simple JWT authentication
- jobs queuing
"""
    )
)


def init_app(app):
    """Initializes all ENABLED_MODULES and the Api object."""
    from importlib import import_module

    for module_name in app.config['ENABLED_MODULES']:
        # Import the module's models package before attempting to load its "ns" attribute
        import_module(f'.{module_name}.models', package=__name__)

        ns = import_module(f'.{module_name}.resources', package=__name__).ns
        api.add_namespace(ns, path=f'/{module_name}')

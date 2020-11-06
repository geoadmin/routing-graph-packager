import os
from importlib import import_module

from flask import Blueprint
from flask_restx import Api
from flask_restx.errors import HTTPStatus
from werkzeug.exceptions import (
    NotFound, BadRequest, Conflict, Forbidden, Unauthorized, InternalServerError
)

from .__version__ import __version__, __api_suffix__, __description__
# Re-export the models and jobs for easier import in other modules
from .jobs.models import Job
from .users.models import User


cwd = os.path.abspath(os.path.dirname(__file__))

bp = Blueprint(f'api_{__api_suffix__}', __name__, url_prefix=f'/api/{__api_suffix__}')

auth = {'basic': {'type': 'basic'}}

api = Api(
    bp,
    authorizations=auth,
    version=__version__,
    title='KADAS Routing Tile Generator',
    description=__description__
)


# Add some custom error handlers to make the error response consistent
@api.errorhandler(NotFound)
def handle_user_no_sql_result_error(e: NotFound):
    return {'error': 'Entity not found.'}, HTTPStatus.NOT_FOUND


@api.errorhandler(Unauthorized)
def handle_user_forbidden_error(e: Unauthorized):
    return {'error': e.description}, HTTPStatus.UNAUTHORIZED


@api.errorhandler(Forbidden)
def handle_user_forbidden_error(e: Forbidden):
    return {'error': e.description}, HTTPStatus.FORBIDDEN


@api.errorhandler(BadRequest)
def handle_user_bad_post_error(e: BadRequest):
    return {'error': e.description}, HTTPStatus.BAD_REQUEST


@api.errorhandler(Conflict)
def handle_user_conflict_error(e: Conflict):
    return {'error': e.description}, HTTPStatus.CONFLICT


@api.errorhandler(InternalServerError)
def handle_job_server_error(e):
    return {'error': e.description}, HTTPStatus.INTERNAL_SERVER_ERROR


def init_app(app):
    """Initializes all ENABLED_MODULES and the Api object."""

    for module_name in os.listdir(cwd):
        module_path = os.path.join(cwd, module_name)
        if 'pycache' in module_name or not os.path.isdir(module_path):
            continue
        # Import the module's models package before attempting to load its "ns" attribute
        import_module(f'.{module_name}.models', package=__name__)

        ns = import_module(f'.{module_name}.resources', package=__name__).ns
        api.add_namespace(ns, path=f'/{module_name}')

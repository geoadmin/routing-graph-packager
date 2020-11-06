import os
import logging

from flask import current_app
from flask_restx import Resource, Namespace, fields, reqparse
from flask_restx.errors import HTTPStatus
from werkzeug.exceptions import BadRequest
from geoalchemy2.shape import to_shape

from ...auth.basic_auth import basic_auth
from ...db_utils import add_or_abort
from . import JobFields
from .models import Job
from .validate import validate_post
from ...core.geometries.geom_conversions import bbox_to_wkt

# Mandatory, will be added by api_vX.__init__
ns = Namespace('jobs', description='Job related operations')

# Parse POST request
parser = reqparse.RequestParser()
parser.add_argument(JobFields.NAME)
parser.add_argument(JobFields.DESCRIPTION)
parser.add_argument(JobFields.BBOX)
parser.add_argument(JobFields.PROVIDER)
parser.add_argument(JobFields.ROUTER)
parser.add_argument(JobFields.SCHEDULE)


class BboxField(fields.Raw):
    __schema_type__ = 'string'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, example='1.531906,42.559908,1.6325,42.577608')

    def format(self, value):
        geom = to_shape(value)
        bbox = geom.bounds

        return ','.join([str(x) for x in bbox])


job_base_schema = ns.model(
    'JobBase',
    {
        JobFields.NAME: fields.String(example='Switzerland'),
        JobFields.DESCRIPTION: fields.String(example='OSM road network of Switzerland'),
        JobFields.PROVIDER: fields.String(example='osm'),
        JobFields.ROUTER: fields.String(example='valhalla'),
        JobFields.BBOX: BboxField(),
        JobFields.SCHEDULE: fields.String(example='daily'),
    }
)

job_response_schema = ns.clone(
    'JobResp', {
        JobFields.ID: fields.Integer,
        JobFields.USER_ID: fields.Integer,
        JobFields.STATUS: fields.String(example='completed')
    }, job_base_schema
)


@ns.route('/')
@ns.response(HTTPStatus.INTERNAL_SERVER_ERROR, 'Unknown error.')
class Jobs(Resource):
    """Manipulates User table"""
    @basic_auth.login_required
    @ns.doc(security='basic')
    @ns.expect(job_base_schema)
    @ns.marshal_with(job_response_schema)
    @ns.response(HTTPStatus.UNAUTHORIZED, 'Invalid/missing basic authorization.')
    def post(self):
        """POST a new job. Needs admin privileges"""

        # avoid circular imports
        from ...tasks import create_package

        args = parser.parse_args(strict=True)
        validate_post(args)
        router_name = args[JobFields.ROUTER]
        provider = args[JobFields.PROVIDER]

        if router_name not in current_app.config['ENABLED_ROUTERS']:
            raise BadRequest(f"Routing engine '{router_name}' is not enabled.")
        if provider not in current_app.config['ENABLED_PROVIDERS']:
            raise BadRequest(f"Provider '{provider}' is not enabled.")

        current_user = basic_auth.current_user()

        job = Job(
            name=args[JobFields.NAME],
            description=args[JobFields.DESCRIPTION],
            provider=args[JobFields.PROVIDER],
            router=args[JobFields.ROUTER],
            user_id=current_user.id,
            schedule=args[JobFields.SCHEDULE],
            status='Starting'
        )

        bbox = [float(x) for x in args[JobFields.BBOX].split(',')]
        job.set_bbox_wkt(bbox_to_wkt(bbox))

        add_or_abort(job)

        # launch Redis task
        current_app.task_queue.enqueue(create_package, router_name, job.id, current_user.email)

        return job

    @ns.marshal_list_with(job_response_schema)
    def get(self):
        """GET all jobs"""
        return Job.query.all()


@ns.route('/<int:id>')
@ns.response(HTTPStatus.INTERNAL_SERVER_ERROR, 'Unknown error.')
@ns.response(HTTPStatus.NOT_FOUND, 'Unknown job id.')
class JobSingle(Resource):
    """Get or delete single jobs"""
    @ns.marshal_with(job_response_schema)
    def get(self, id):
        """GET a single job"""
        return Job.query.get_or_404(id)

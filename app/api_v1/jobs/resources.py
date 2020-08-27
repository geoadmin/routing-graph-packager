import os
import logging

from flask import current_app, g
from flask_restx import Resource, Namespace, fields, reqparse
from flask_restx.errors import HTTPStatus
from werkzeug.exceptions import NotFound, BadRequest, InternalServerError
from geoalchemy2.shape import to_shape
from docker.errors import ImageNotFound

from app.auth.basic_auth import basic_auth
from ...db_utils import add_or_abort
from ...cmd_utils import osmium_extract_proc
from . import JobFields
from .models import Job
from .validate import validate_post
from ...core.geometries.geom_conversions import bbox_to_wkt
from ...core.routers import get_router
from ...logger import AppSmtpHandler, get_smtp_details

# Mandatory, will be added by api_vX.__init__
ns = Namespace('jobs', description='Job related operations')

# Parse POST request
parser = reqparse.RequestParser()
parser.add_argument(JobFields.NAME)
parser.add_argument(JobFields.DESCRIPTION)
parser.add_argument(JobFields.BBOX)
parser.add_argument(JobFields.PROVIDER)
parser.add_argument(JobFields.ROUTER)
# parser.add_argument(JobFields.SCHEDULE)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


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
        # JobFields.SCHEDULE: fields.String,
    }
)

job_response_schema = ns.clone(
    'JobResp', {
        JobFields.ID:
        fields.Integer,
        JobFields.USER_ID:
        fields.Integer,
        JobFields.CONTAINER_ID:
        fields.String(example='91a0c3c3b5408e6fba35834b1bc9402f5183b81b49eddf3da8fe2cc5fcd1ed18'),
        JobFields.STATUS:
        fields.String(example='completed')
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
            user_id=current_user.id
        )

        bbox = [float(x) for x in args[JobFields.BBOX].split(',')]
        job.set_bbox_geojson(bbox_to_wkt(bbox))

        in_pbf_path = current_app.config['PBF_PATH']
        out_pbf_dir = current_app.config['PBF_TEMP_DIR']
        cut_pbf_path = os.path.join(out_pbf_dir, f'{router_name}_cut.pbf')

        # Cut the PBF to the bbox extent
        try:
            osmium_proc = osmium_extract_proc(bbox, in_pbf_path, cut_pbf_path)
        except FileNotFoundError:
            raise InternalServerError("'osmium' is not installed on the host.")

        osmium_status = osmium_proc.wait()
        if osmium_status:
            msg = f"'osmium': {osmium_proc.stderr.read().decode()}"
            logger.error(msg)
            raise InternalServerError(msg)

        # Build the graph
        router = get_router(router_name, cut_pbf_path)
        if not router:
            raise BadRequest(f"'{router_name}' is not a valid routing engine.")

        handler = AppSmtpHandler(**get_smtp_details(current_app.config, [current_user.email], False))
        handler.setLevel(logging.INFO)
        logger.addHandler(handler)

        try:
            exit_code, output = router.build_graph()
        except ImageNotFound:
            raise InternalServerError(f"Docker image {router.image} not found for '{router.name}'")

        job.set_container_id(router.container_id)
        if exit_code:
            job.set_status('failed')
            add_or_abort(job)
            msg = f"'{router_name}': {output.decode()}"
            logger.error(msg, extra=dict(router=router_name, container_id=router.container_id))
            raise InternalServerError(f"'{router_name}': {output.decode()}")

        job.set_status('completed')
        add_or_abort(job)
        logger.info(f"Job {job.id} by {current_user.email} finished successfully.")

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

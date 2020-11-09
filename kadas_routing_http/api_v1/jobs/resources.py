from flask import current_app
from flask_restx import Resource, Namespace, fields, reqparse
from flask_restx.errors import HTTPStatus
from sqlalchemy import func
from geoalchemy2.shape import to_shape
from rq.registry import NoSuchJobError
from rq.job import Job as RqJob

from ...auth.basic_auth import basic_auth
from ...constants import STATUSES
from ...db_utils import add_or_abort, delete_or_abort
from . import *
from .models import Job
from .validate import validate_post, validate_get
from ...core.geometries.geom_conversions import bbox_to_wkt

# Mandatory, will be added by api_vX.__init__
ns = Namespace('jobs', description='Job related operations')

# Parse POST request
post_parser = reqparse.RequestParser()
post_parser.add_argument(JobFields.NAME)
post_parser.add_argument(JobFields.DESCRIPTION)
post_parser.add_argument(JobFields.BBOX)
post_parser.add_argument(JobFields.PROVIDER)
post_parser.add_argument(JobFields.ROUTER)
post_parser.add_argument(JobFields.INTERVAL)
post_parser.add_argument(JobFields.COMPRESSION)

get_parser = reqparse.RequestParser()
get_parser.add_argument(JobFields.PROVIDER)
get_parser.add_argument(JobFields.ROUTER)
get_parser.add_argument(JobFields.BBOX)
get_parser.add_argument(JobFields.STATUS)


class BboxField(fields.Raw):
    __schema_type__ = 'string'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def format(self, value):
        geom = to_shape(value)
        bbox = geom.bounds

        return ','.join([str(x) for x in bbox])


job_get_schema = ns.model(
    'JobGet',
    {
        JobFields.PROVIDER: fields.String(example='osm', location='args'),
        JobFields.ROUTER: fields.String(example='valhalla', location='args'),
        JobFields.BBOX: BboxField(example='1.531906,42.559908,1.6325,42.577608', location='args'),
        JobFields.INTERVAL: fields.String(example='daily', location='args'),
    }
)

job_base_schema = ns.model(
    'JobBase',
    {
        JobFields.NAME: fields.String(example='Switzerland'),
        JobFields.DESCRIPTION: fields.String(example='OSM road network of Switzerland'),
        JobFields.PROVIDER: fields.String(example='osm'),
        JobFields.ROUTER: fields.String(example='valhalla'),
        JobFields.BBOX: BboxField(example='1.531906,42.559908,1.6325,42.577608'),
        JobFields.INTERVAL: fields.String(example='daily'),
        JobFields.COMPRESSION: fields.String(example='zip')
    }
)

job_response_schema = ns.clone(
    'JobResp', {
        JobFields.ID: fields.Integer(example=0),
        JobFields.USER_ID: fields.Integer(example=0),
        JobFields.STATUS: fields.String(example='completed', enum=STATUSES),
        JobFields.RQ_ID: fields.String(example='ac277aaa-c6e1-4660-9a43-38864ccabd42', attribute='rq_id'),
        JobFields.CONTAINER_ID: fields.String(example='6f5747f3cb03cc9add39db9b737d4138fcc1d821319cdf3ec0aea5735f3652c7'),
        JobFields.LAST_RAN: fields.DateTime(example='')
    }, job_base_schema
)


@ns.route('/')
@ns.response(HTTPStatus.INTERNAL_SERVER_ERROR, 'Unknown error.')
class Jobs(Resource):
    """Manipulates User table"""

    @ns.marshal_list_with(job_response_schema)
    @ns.expect(job_get_schema)
    def get(self):
        """GET all jobs."""
        args = get_parser.parse_args()
        validate_get(args)

        # collect all filters
        filters = []

        bbox = args.get(JobFields.BBOX)
        if bbox:
            bbox = [float(x) for x in args[JobFields.BBOX].split(',')]
            bbox_wkt = bbox_to_wkt(bbox)
            filters.append(func.ST_Intersects(Job.bbox, bbox_wkt))

        router = args.get(JobFields.ROUTER)
        if router:
            filters.append(Job.router == router)

        provider = args.get(JobFields.PROVIDER)
        if provider:
            filters.append(Job.provider == provider)

        status = args.get(JobFields.STATUS)
        if status:
            filters.append(Job.status == status)

        return Job.query.filter(*filters).all()

    @basic_auth.login_required
    @ns.doc(security='basic')
    @ns.expect(job_base_schema)
    @ns.marshal_with(job_response_schema)
    @ns.response(HTTPStatus.UNAUTHORIZED, 'Invalid/missing basic authorization.')
    def post(self):
        """POST a new job. Needs admin privileges."""

        # avoid circular imports
        from ...tasks import create_package

        args = post_parser.parse_args(strict=True)
        validate_post(args)
        router_name = args[JobFields.ROUTER]

        current_user = basic_auth.current_user()

        job = Job(
            name=args[JobFields.NAME],
            description=args[JobFields.DESCRIPTION],
            provider=args[JobFields.PROVIDER],
            router=args[JobFields.ROUTER],
            user_id=current_user.id,
            interval=args[JobFields.INTERVAL],
            status='Starting',
            compression=args[JobFields.COMPRESSION]
        )

        bbox = [float(x) for x in args[JobFields.BBOX].split(',')]
        job.set_bbox_wkt(bbox_to_wkt(bbox))

        add_or_abort(job)

        # launch Redis task and update db entries there
        current_app.task_queue.enqueue(create_package, router_name, job.id, current_user.email)

        return job


@ns.route('/<int:id>')
@ns.response(HTTPStatus.INTERNAL_SERVER_ERROR, 'Unknown error.')
@ns.response(HTTPStatus.NOT_FOUND, 'Unknown job id.')
class JobSingle(Resource):
    """Get or delete single jobs"""
    @ns.marshal_with(job_response_schema)
    def get(self, id):
        """GET a single job."""
        return Job.query.get_or_404(id)

    @basic_auth.login_required
    @ns.doc(security='basic')
    @ns.response(HTTPStatus.NO_CONTENT, 'Success, no content.')
    @ns.response(HTTPStatus.UNAUTHORIZED, 'Invalid/missing basic authorization.')
    def delete(self, id):
        """DELETE a single job. Will also stop the job if it's in progress. Needs admin privileges."""
        db_job: Job = Job.query.get_or_404(id)

        # try to delete the Redis job or don't care if there is none
        try:
            rq_job = RqJob.fetch(db_job.rq_id, connection=current_app.redis)
            if rq_job.get_status() in ('queued', 'started'):
                rq_job.delete()
        except NoSuchJobError:
            pass

        delete_or_abort(db_job)

        return '', HTTPStatus.NO_CONTENT

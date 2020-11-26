from datetime import datetime
import os

from flask import current_app, g
from flask_restx import Resource, Namespace, fields, reqparse
from flask_restx.errors import HTTPStatus
from sqlalchemy import func
from geoalchemy2.shape import to_shape
from rq.registry import NoSuchJobError
from rq.job import Job as RqJob

from . import JobFields
from .models import Job
from .validate import validate_post, validate_get
from ...auth.basic_auth import basic_auth
from ...utils.db_utils import add_or_abort, delete_or_abort
from ...utils.geom_utils import bbox_to_wkt
from ...utils.file_utils import make_package_path
from ...constants import *

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
get_parser.add_argument(JobFields.INTERVAL)


class BboxField(fields.Raw):
    __schema_type__ = 'string'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def format(self, value):
        geom = to_shape(value)
        bbox = geom.bounds

        return ','.join([str(x) for x in bbox])


job_base_schema = ns.model(
    'JobBase', {
        JobFields.NAME: fields.String(example='Switzerland'),
        JobFields.DESCRIPTION: fields.String(example='OSM road network of Switzerland'),
        JobFields.PROVIDER: fields.String(example=Providers.OSM.value),
        JobFields.ROUTER: fields.String(example=Routers.VALHALLA.value),
        JobFields.BBOX: BboxField(example='1.531906,42.559908,1.6325,42.577608'),
        JobFields.INTERVAL: fields.String(example=Intervals.DAILY.value),
        JobFields.COMPRESSION: fields.String(example=Compressions.ZIP.value)
    }
)

job_response_schema = ns.clone(
    'JobResp', {
        JobFields.ID:
        fields.Integer(example=0),
        JobFields.USER_ID:
        fields.Integer(example=0),
        JobFields.STATUS:
        fields.String(example=Statuses.COMPLETED.value),
        JobFields.RQ_ID:
        fields.String(example='ac277aaa-c6e1-4660-9a43-38864ccabd42', attribute='rq_id'),
        JobFields.CONTAINER_ID:
        fields.String(example='6f5747f3cb03cc9add39db9b737d4138fcc1d821319cdf3ec0aea5735f3652c7'),
        JobFields.LAST_STARTED:
        fields.DateTime(example='2020-11-16T13:03:31.598Z'),
        JobFields.LAST_FINISHED:
        fields.DateTime(example='2020-11-16T13:06:33.310Z'),
        JobFields.PATH:
        fields.String(example='/root/routing-packager/data/valhalla/valhalla_tomtom_andorra.zip'),
        JobFields.PBF_PATH:
        fields.String(example='/root/routing-packager/data/osm/cut_andorra-latest.osm.pbf')
    }, job_base_schema
)


@ns.route('/')
@ns.response(HTTPStatus.BAD_REQUEST, 'Invalid request parameters.')
@ns.response(HTTPStatus.INTERNAL_SERVER_ERROR, 'Unknown error.')
class Jobs(Resource):
    """Manipulates User table"""
    @ns.doc(
        params={
            JobFields.ROUTER: {
                'in': 'query',
                'description': 'Filter for routing engine.',
                "enum": ROUTERS
            },
            JobFields.PROVIDER: {
                'in': 'query',
                'description': 'Filter for data provider.',
                "enum": PROVIDERS
            },
            JobFields.BBOX: {
                'in': 'query',
                'description': 'Filter for bbox, e.g. "0.531906,4559908,0.6325,42.577608".'
            },
            JobFields.INTERVAL: {
                'in': 'query',
                'description': 'Filter for update interval.',
                "enum": INTERVALS
            },
            JobFields.STATUS: {
                'in': 'query',
                'description': 'Filter for job status.',
                "enum": STATUSES
            }
        }
    )
    @ns.marshal_list_with(job_response_schema)
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

        interval = args.get(JobFields.INTERVAL)
        if interval:
            filters.append(Job.interval == interval)

        status = args.get(JobFields.STATUS)
        if status:
            filters.append(Job.status == status)

        return Job.query.filter(*filters).all()

    @basic_auth.login_required
    @ns.doc(security='basic')
    @ns.expect(job_base_schema)
    @ns.marshal_with(job_response_schema)
    @ns.response(HTTPStatus.FORBIDDEN, 'Access forbidden.')
    @ns.response(HTTPStatus.UNAUTHORIZED, 'Invalid/missing basic authorization.')
    def post(self):
        """POST a new job. Needs admin privileges."""

        # avoid circular imports
        from ...tasks import create_package

        args = post_parser.parse_args(strict=True)
        # Sanitize the name field a little
        args[JobFields.NAME] = args[JobFields.NAME].strip().replace(' ', '_')
        validate_post(args)

        router_name = args[JobFields.ROUTER]
        dataset_name = args[JobFields.NAME]
        provider = args[JobFields.PROVIDER]
        compression = args[JobFields.COMPRESSION]
        bbox = [float(x) for x in args[JobFields.BBOX].split(',')]
        description = args[JobFields.DESCRIPTION]

        current_user = basic_auth.current_user()

        data_dir = current_app.config['DATA_DIR']
        result_path = make_package_path(data_dir, dataset_name, router_name, provider, compression)

        job = Job(
            name=dataset_name,
            description=description,
            provider=provider,
            router=router_name,
            user_id=current_user.id,
            interval=args[JobFields.INTERVAL],
            status='Queued',
            compression=compression,
            bbox=bbox_to_wkt(bbox),
            path=result_path,
            last_started=datetime.utcnow()
        )

        add_or_abort(job)

        # Ugly but hey.. We ideally have the output PBF named after the job ID
        pbf_path = os.path.join(data_dir, provider, f"{job.id}.{provider}.pbf")
        job.set_pbf_path(pbf_path)
        session = g.db.session
        session.add(job)
        session.commit()

        # launch Redis task and update db entries there
        # for testing we don't want that behaviour
        if not current_app.testing:  # pragma: no cover
            current_app.task_queue.enqueue(
                create_package, job.id, dataset_name, description, router_name, provider, bbox,
                result_path, pbf_path, compression, current_user.email,
                current_app.config['FLASK_CONFIG']
            )

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
    @ns.response(HTTPStatus.FORBIDDEN, 'Access forbidden.')
    @ns.response(HTTPStatus.UNAUTHORIZED, 'Invalid/missing basic authorization.')
    def delete(self, id):
        """DELETE a single job. Will also stop the job if it's in progress. Needs admin privileges."""
        db_job: Job = Job.query.get_or_404(id)

        # try to delete the Redis job or don't care if there is none
        try:
            rq_job = RqJob.fetch(db_job.rq_id, connection=current_app.redis)
            if rq_job.get_status() in ('queued', 'started'):  # pragma: no cover
                rq_job.delete()
        except NoSuchJobError:
            pass

        delete_or_abort(db_job)
        if os.path.exists(db_job.pbf_path):
            os.remove(db_job.pbf_path)

        return '', HTTPStatus.NO_CONTENT

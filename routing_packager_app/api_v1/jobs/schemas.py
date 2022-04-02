from flask_restx import fields
from geoalchemy2.shape import to_shape

from . import JobFields, OsmFields
from ...constants import Providers, Routers, Intervals, Compressions, Statuses


class BboxField(fields.Raw):
    __schema_type__ = "string"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def format(self, value):
        geom = to_shape(value)
        bbox = geom.bounds

        return ",".join([str(x) for x in bbox])


job_base_schema = {
    JobFields.NAME: fields.String(example="Switzerland"),
    JobFields.DESCRIPTION: fields.String(example="OSM road network of Switzerland"),
    JobFields.PROVIDER: fields.String(example=Providers.OSM.value),
    JobFields.ROUTER: fields.String(example=Routers.VALHALLA.value),
    JobFields.BBOX: BboxField(example="1.531906,42.559908,1.6325,42.577608"),
    JobFields.INTERVAL: fields.String(example=Intervals.DAILY.value),
    JobFields.COMPRESSION: fields.String(example=Compressions.ZIP.value),
}

job_response_schema = {
    JobFields.ID: fields.Integer(example=0),
    JobFields.USER_ID: fields.Integer(example=0),
    JobFields.STATUS: fields.String(example=Statuses.COMPLETED.value),
    JobFields.RQ_ID: fields.String(example="ac277aaa-c6e1-4660-9a43-38864ccabd42", attribute="rq_id"),
    JobFields.CONTAINER_ID: fields.String(
        example="6f5747f3cb03cc9add39db9b737d4138fcc1d821319cdf3ec0aea5735f3652c7"
    ),
    JobFields.LAST_STARTED: fields.DateTime(example="2020-11-16T13:03:31.598Z"),
    JobFields.LAST_FINISHED: fields.DateTime(example="2020-11-16T13:06:33.310Z"),
    JobFields.PATH: fields.String(
        example="/root/routing-packager/data/valhalla/valhalla_tomtom_andorra.zip"
    ),
    JobFields.PBF_PATH: fields.String(
        example="/root/routing-packager/data/osm/cut_andorra-latest.osm.pbf"
    ),
}

osm_response_schema = {
    OsmFields.FILEPATH: fields.String(example="data/osm/andorra-latest-test.osm.pbf"),
    OsmFields.TIMESTAMP: fields.String(example="2020-12-07T15:46:52Z"),
    OsmFields.BBOX: fields.String(example="1.531906,42.559908,1.6325,42.577608"),
    OsmFields.SIZE: fields.Integer(example=275483),
}

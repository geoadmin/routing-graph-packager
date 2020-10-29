from geoalchemy2 import Geography

from ... import db


class Job(db.Model):

    __tablename__ = 'jobs'

    id = db.Column(db.Integer, primary_key=True)
    container_id = db.Column(db.String, nullable=False)
    status = db.Column(db.String, nullable=False)
    name = db.Column(db.String, nullable=False)
    description = db.Column(db.String)
    provider = db.Column(db.String, nullable=False)
    router = db.Column(db.String, nullable=False)
    bbox = db.Column(Geography("POLYGON", srid=4326), nullable=False)
    # schedule = db.Column(db.String, nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    def __repr__(self):  # pragma: no cover
        s = f'<Job id={self.id} pid={self.pid} status={self.status} '
        f'router={self.router}>'
        return s

    def set_bbox_geojson(self, bbox_geojson):
        """

        :param dict bbox_geojson: comma-delimited string of minx,miny,maxx,maxy
        """
        self.bbox = bbox_geojson

    def set_status(self, status):
        self.status = status

    def set_container_id(self, container_id):
        self.container_id = container_id

from geoalchemy2 import Geography

from ... import db


class Job(db.Model):

    __tablename__ = 'jobs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    rq_id = db.Column(db.String, nullable=True)
    container_id = db.Column(db.String, nullable=True)
    name = db.Column(db.String, nullable=False)
    description = db.Column(db.String)
    status = db.Column(db.String, nullable=False)
    provider = db.Column(db.String, nullable=False)
    router = db.Column(db.String, nullable=False)  # router name, i.e. valhalla, graphhopper, ors etc
    bbox = db.Column(Geography("POLYGON", srid=4326, spatial_index=True), nullable=False)
    interval = db.Column(db.String, nullable=False)  # daily, weekly, monthly, yearly
    compression = db.Column(db.String, nullable=False)  # zip, tar etc
    last_ran = db.Column(db.DateTime, nullable=True)  # did it ever run?

    def __repr__(self):  # pragma: no cover
        s = f'<Job id={self.id} status={self.status} schedule={self.schedule} router={self.router}>'
        return s

    def set_bbox_wkt(self, bbox_wkt: str):
        self.bbox = bbox_wkt

    def set_status(self, status: str):
        self.status = status

    def set_container_id(self, container_id: str):
        self.container_id = container_id

    def set_rq_id(self, rq_id: str):
        self.rq_id = rq_id

    def set_last_ran(self, dt):
        self.last_ran = dt

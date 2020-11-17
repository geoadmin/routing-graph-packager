from geoalchemy2 import Geography

from ... import db


class Job(db.Model):

    __tablename__ = 'jobs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    rq_id = db.Column(db.String, nullable=True)
    container_id = db.Column(db.String, nullable=True)
    name = db.Column(db.String, nullable=False)
    description = db.Column(db.String, nullable=True)
    status = db.Column(db.String, nullable=False)
    provider = db.Column(db.String, nullable=False)
    router = db.Column(db.String, nullable=False)  # router name, i.e. valhalla, graphhopper, ors etc
    bbox = db.Column(Geography("POLYGON", srid=4326, spatial_index=True), nullable=False)
    interval = db.Column(db.String, nullable=False, index=True)  # daily, weekly, monthly, yearly
    compression = db.Column(db.String, nullable=False)  # zip, tar etc
    last_started = db.Column(db.DateTime, nullable=False)  # did it ever run?
    last_finished = db.Column(db.DateTime, nullable=True)  # did it ever finish?
    path = db.Column(db.String, nullable=False)
    pbf_path = db.Column(db.String, nullable=True)

    def __repr__(self):  # pragma: no cover
        s = f'<Job id={self.id} name={self.name} status={self.status} interval={self.interval} provider={self.provider} router={self.router} compression={self.compression}>'
        return s

    def set_status(self, status: str):
        self.status = status

    def set_container_id(self, container_id: str):
        self.container_id = container_id

    def set_rq_id(self, rq_id: str):  # pragma: no cover
        self.rq_id = rq_id

    def set_last_finished(self, dt):
        self.last_finished = dt

    def set_pbf_path(self, path):
        self.pbf_path = path

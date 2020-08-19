from app import db
from sqlalchemy_utils.types import PasswordType


class User(db.Model):

    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    password = db.Column(PasswordType(schemes=('pbkdf2_sha512', )), nullable=False)

    def __repr__(self):
        return '<User {}>'.format(self.email)

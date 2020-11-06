from sqlalchemy_utils.types import PasswordType

from ... import db


class User(db.Model):
    """The users table."""

    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    password = db.Column(PasswordType(schemes=('pbkdf2_sha512', )), nullable=False)

    def __repr__(self):  # pragma: no cover
        return '<User {}>'.format(self.email)

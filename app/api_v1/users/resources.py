from flask_restx import Resource, Namespace, fields, reqparse
from flask_restx.errors import HTTPStatus
from werkzeug.exceptions import NotFound, BadRequest

from app import db
from .models import User
from . import UserFields
from ...db_utils import add_or_abort

# Mandatory, will be added by api_vX.__init__
ns = Namespace('users', description='User related operations')

# Parse POST request
parser = reqparse.RequestParser()
parser.add_argument(UserFields.EMAIL, help='Email is equivalent to username.', required=True)
parser.add_argument(UserFields.PASSWORD, help='No password rules apply.', required=True)

user_schema = ns.model('User', {
    UserFields.ID: fields.Integer,
    UserFields.EMAIL: fields.String,
})


@ns.route('/')
@ns.response(HTTPStatus.INTERNAL_SERVER_ERROR, 'Unknown error.')
class UserRegistration(Resource):
    """Manipulates User table"""
    @ns.marshal_with(user_schema)
    @ns.response(HTTPStatus.CONFLICT, 'User already exists.')
    def post(self):
        """Create a new user"""
        new_user = User(**parser.parse_args(strict=True))
        add_or_abort(new_user)
        return new_user

    @ns.marshal_list_with(user_schema)
    def get(self):
        """GET all users"""
        return User.query.all()


@ns.route('/<int:id>')
@ns.response(HTTPStatus.INTERNAL_SERVER_ERROR, 'Unknown error.')
class UserSingle(Resource):
    """Get or delete single users"""
    @ns.marshal_with(user_schema)
    @ns.response(HTTPStatus.NOT_FOUND, 'Unknown user id.')
    def get(self, id):
        """GET a single user"""
        return User.query.get_or_404(id)

    def delete(self, id):
        """DELETE a user"""
        db.session.delete(User.query.get_or_404(id))
        db.session.commit()
        return '', HTTPStatus.NO_CONTENT


# Some error handlers
@ns.errorhandler(NotFound)
def handle_no_sql_result_error(e: NotFound):
    return {'error': 'User not found.'}, HTTPStatus.NOT_FOUND


@ns.errorhandler(BadRequest)
def handle_bad_post_error(e: BadRequest):
    return {'error': e.description}, HTTPStatus.BAD_REQUEST

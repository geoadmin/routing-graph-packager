from flask import g, current_app
from flask_restx import Resource, Namespace, fields, reqparse
from flask_restx.errors import HTTPStatus
from werkzeug.exceptions import Conflict, Forbidden

from .models import User
from . import UserFields
from .validate import validate_post
from ...auth.basic_auth import basic_auth
from ...utils.db_utils import add_or_abort

# Mandatory, will be added by api_vX.__init__
ns = Namespace('users', description='User related operations')

# Parse POST request
parser = reqparse.RequestParser()
parser.add_argument(UserFields.EMAIL)
parser.add_argument(UserFields.PASSWORD)

# Set up different schemas for request and response
user_base_schema = ns.model(
    'UserBase', {
        UserFields.EMAIL: fields.String(example='example@email.org'),
    }
)
user_response_schema = ns.clone('UserResp', user_base_schema, {UserFields.ID: fields.Integer})
user_body_schema = ns.clone('UserReq', user_base_schema, {UserFields.PASSWORD: fields.String})


@ns.route('/')
@ns.response(HTTPStatus.INTERNAL_SERVER_ERROR, 'Unknown error.')
class UserRegistration(Resource):
    """Manipulates User table"""
    @basic_auth.login_required
    @ns.doc(security='basic')
    @ns.expect(user_body_schema)
    @ns.marshal_with(user_response_schema)
    @ns.response(HTTPStatus.CONFLICT, 'User already exists.')
    @ns.response(HTTPStatus.UNAUTHORIZED, 'Invalid/missing basic authorization.')
    def post(self):
        """POST a new user. Needs admin privileges"""
        args = parser.parse_args(strict=True)
        validate_post(args)

        new_user = User(**args)
        add_or_abort(new_user)
        return new_user

    @ns.marshal_list_with(user_response_schema)
    def get(self):
        """GET all users."""
        return User.query.all()


@ns.route('/<int:id>')
@ns.response(HTTPStatus.INTERNAL_SERVER_ERROR, 'Unknown error.')
@ns.response(HTTPStatus.NOT_FOUND, 'Unknown user id.')
class UserSingle(Resource):
    """Get or delete single users"""
    @ns.marshal_with(user_response_schema)
    def get(self, id):
        """GET a single user"""
        return User.query.get_or_404(id)

    @basic_auth.login_required
    @ns.doc(security='basic')
    @ns.response(HTTPStatus.NO_CONTENT, 'Success, no content.')
    @ns.response(HTTPStatus.UNAUTHORIZED, 'Invalid/missing basic authorization.')
    @ns.response(HTTPStatus.FORBIDDEN, 'Access forbidden.')
    @ns.response(HTTPStatus.CONFLICT, 'Conflict detected.')
    def delete(self, id):
        """DELETE a user. Needs admin privileges."""
        db = g.db
        user = User.query.get_or_404(id)
        current_user_email = basic_auth.current_user().email

        admin_email = current_app.config['ADMIN_EMAIL']
        if admin_email == user.email:
            raise Conflict("Can't delete admin user.")
        elif not admin_email == current_user_email:
            raise Forbidden("Admin privileges are required to delete a user.")

        db.session.delete(User.query.get_or_404(id))
        db.session.commit()
        return '', HTTPStatus.NO_CONTENT

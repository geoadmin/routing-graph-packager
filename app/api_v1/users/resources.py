from flask import g
from flask_restx import Resource, Namespace, fields, reqparse, abort
from flask_restx.errors import HTTPStatus
from werkzeug.exceptions import NotFound, BadRequest
import re

from .models import User
from . import UserFields
from app.auth.basic_auth import basic_auth
from ...db_utils import add_or_abort

# Mandatory, will be added by api_vX.__init__
ns = Namespace('users', description='User related operations')

# Parse POST request
parser = reqparse.RequestParser()
parser.add_argument(UserFields.EMAIL)
parser.add_argument(UserFields.PASSWORD)

user_base_schema = ns.model('UserBase', {
    UserFields.EMAIL: fields.String,
})
user_response_schema = ns.clone('UserResp', user_base_schema, {UserFields.ID: fields.Integer})
user_body_schema = ns.clone('UserReq', user_base_schema, {UserFields.PASSWORD: fields.String})


@ns.route('/')
@ns.response(HTTPStatus.INTERNAL_SERVER_ERROR, 'Unknown error.')
class UserRegistration(Resource):
    """Manipulates User table"""
    @basic_auth.login_required
    @ns.expect(user_body_schema)
    @ns.marshal_with(user_response_schema)
    @ns.response(HTTPStatus.CONFLICT, 'User already exists.')
    @ns.response(HTTPStatus.UNAUTHORIZED, 'Invalid/missing basic authorization.')
    def post(self):
        """POST a new user. Needs admin privileges"""
        args = parser.parse_args(strict=True)
        for arg, value in args.items():
            if not value:
                raise BadRequest(f"'{arg}' is required in request.")

        # Validate email
        email_re = '^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\D{2,3})+$'
        if not re.search(email_re, args['email']):
            raise BadRequest(f'Email \'{args["email"]}\' is invalid.')

        new_user = User(**args)
        add_or_abort(new_user)
        return new_user

    @ns.marshal_list_with(user_response_schema)
    def get(self):
        """GET all users"""
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
    @ns.response(HTTPStatus.NO_CONTENT, 'Success, no content.')
    def delete(self, id):
        """DELETE a user"""
        db = g.db
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

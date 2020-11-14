import re

from werkzeug.exceptions import BadRequest, Conflict, Forbidden
from flask import current_app

from . import UserFields
from .models import User
from ...auth.basic_auth import basic_auth


def validate_post(args):
    """
    Validates the POST request parameters.

    :param dict args: request parameters
    """
    admin_email = current_app.config['ADMIN_EMAIL']
    if not admin_email == basic_auth.current_user().email:
        raise Forbidden("Admin privileges are required to register a new user.")

    for arg, value in args.items():
        if not value:
            raise BadRequest(f"'{arg}' is required in request.")

    # Validate email
    email_re = r'^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\D{2,3})+$'
    if not re.search(email_re, args['email']):
        raise BadRequest(f'Email \'{args["email"]}\' is invalid.')

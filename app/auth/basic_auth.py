from flask_httpauth import HTTPBasicAuth
from flask_restx.errors import HTTPStatus

basic_auth = HTTPBasicAuth()


@basic_auth.verify_password
def verify(email, password):
    """Verify """
    if not (email and password):
        return False

    from ..api_v1.users.models import User
    registered_user: User = User.query.filter_by(email=email).first()
    if not registered_user or not registered_user.password == password:
        return False

    return registered_user


@basic_auth.error_handler
def auth_error(status):
    """Customize the error response of this package to our common schema."""
    msg = 'Access denied.'
    # 401
    if status == HTTPStatus.UNAUTHORIZED:
        msg = "Missing Basic Auth authorization header."
    return {"error": msg}, status

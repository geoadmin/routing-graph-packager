from flask_httpauth import HTTPBasicAuth

basic_auth = HTTPBasicAuth()


@basic_auth.verify_password
def verify(email, password):
    if not (email and password):
        return False

    from ..api_v1.users.models import User
    admin_user: User = User.query.filter_by(email=email).first()
    if not admin_user or not admin_user.password == password:
        return False

    return admin_user

import logging
from flask import current_app, g
from flask_restx import abort
from flask_restx.errors import HTTPStatus
from sqlalchemy import exc

log = logging.getLogger(__name__)


def add_or_abort(obj):
    """
    Commit the database object or abort.

    :param obj: Any database object which needs to be commited.
    """
    session = g.db.session
    success = False
    try:
        session.add(obj)
        session.commit()
        success = True
    except exc.IntegrityError as e:
        log.error(f"Transaction aborted because: {e}")
        abort(code=HTTPStatus.CONFLICT, error="Entity already exists...")
    except Exception as e:  # pragma: no cover
        log.error(f"Transaction aborted because: {e}")
        abort(code=HTTPStatus.INTERNAL_SERVER_ERROR, error=str(e))
    finally:
        if not success:
            session.rollback()


def add_admin_user():
    """Add admin user before first request."""
    admin_email = current_app.config['ADMIN_EMAIL']
    admin_pass = current_app.config['ADMIN_PASS']

    from .api_v1.users.models import User
    if not User.query.filter_by(email=admin_email).first():
        admin_user = User(email=admin_email, password=admin_pass)
        session = g.db.session
        session.add(admin_user)
        session.commit()

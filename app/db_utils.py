import logging
from flask_restx import abort
from flask_restx.errors import HTTPStatus
from sqlalchemy import exc

from app import db

log = logging.getLogger(__name__)

HTTP_EXC = {
    HTTPStatus.CONFLICT.value: {
        "code": HTTPStatus.CONFLICT,
        "error": "Entity already exists, aborting.."
    }
}


def add_or_abort(object):
    """Commit the object or abort"""
    session = db.session
    try:
        session.add(object)
        session.commit()
    except exc.IntegrityError as e:
        log.error(f"Transaction aborted because: {e}")

        session.rollback()
        abort(**HTTP_EXC[HTTPStatus.CONFLICT])
    except Exception as e:  # pragma: no cover
        log.error(f"Transaction aborted because: {e}")

        session.rollback()
        abort(code=HTTPStatus.INTERNAL_SERVER_ERROR, status=str(e))

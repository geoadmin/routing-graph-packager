import logging

from sqlalchemy import exc
from sqlmodel import Session
from starlette.exceptions import HTTPException
from starlette.status import HTTP_409_CONFLICT, HTTP_500_INTERNAL_SERVER_ERROR

LOGGER = logging.getLogger(__name__)


def add_or_abort(db: Session, obj):
    """
    Commit the database object or abort.

    :param db: The DB session.
    :param obj: Any database object which needs to be commited.
    """
    success = False
    try:
        db.add(obj)
        db.commit()
        db.refresh(obj)
        success = True
    except exc.IntegrityError as e:
        LOGGER.error(f"Transaction aborted because: {e}")
        msg = str(e.orig)
        # prettier error message
        needle = "DETAIL: "
        msg_idx = msg.rfind(needle)
        if msg_idx:
            msg = msg[msg_idx + len(needle) + 1 :]
        raise HTTPException(HTTP_409_CONFLICT, str(msg.strip()))
    except Exception as e:  # pragma: no cover
        LOGGER.error(f"Transaction aborted because: {e}")
        raise HTTPException(HTTP_500_INTERNAL_SERVER_ERROR, str(e))
    finally:
        if not success:
            db.rollback()


def delete_or_abort(db: Session, obj):
    """
    Delete the database object or abort.

    :param db: The DB session.
    :param obj: Any database object which needs to be deleted.
    """
    success = False
    try:
        db.delete(obj)
        db.commit()
        success = True
    except Exception as e:  # pragma: no cover
        LOGGER.error(f"Transaction aborted because: {e}")
        raise HTTPException(HTTP_500_INTERNAL_SERVER_ERROR, str(e))
    finally:
        if not success:
            db.rollback()

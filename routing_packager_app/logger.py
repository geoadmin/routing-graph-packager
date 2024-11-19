from logging.handlers import SMTPHandler
import logging
from logging import config
from typing import List  # noqa: F401

from .config import SETTINGS


# https://stackoverflow.com/a/9236722/2582935
class AppSmtpHandler(SMTPHandler):
    """The SMTP handler's extended class to write emails in case of events."""

    def getSubject(self, record: logging.LogRecord) -> str:
        """Alters the subject line of the emails."""
        subject = f"{record.levelname}: "
        if record.levelno == logging.ERROR or record.levelno == logging.CRITICAL:
            subject += f"{record.user}'s job {record.job_id} failed"
        # Warning is only emitted in worker.py, when the deletion fails
        elif record.levelno == logging.WARNING:
            subject += f"{record.user}'s job {record.job_id} was stopped and deleted"
        elif record.levelno == logging.INFO:
            subject += f"{record.user}'s job {record.job_id} succeeded"
        else:
            raise NotImplementedError(
                f"Logger level {record.levelno} is not implemented for this handler."
            )

        return subject

    def emit(self, record):
        """Can be used to limit the emails sent out."""
        super().emit(record)


def get_smtp_details(toaddrs: List[str]):
    """
    Dynamically create the config for the SMTP logger.

    :param toaddrs: The recipients' email addresses.

    :returns: complete SMTP configuration
    :rtype: dict
    """
    # if to_admin:
    #     add_email = config['ADMIN_EMAIL']
    #     if add_email not in toaddrs:
    #         toaddrs.append(config['ADMIN_EMAIL'])

    conf = dict(
        mailhost=(SETTINGS.SMTP_HOST, SETTINGS.SMTP_PORT),
        fromaddr=SETTINGS.SMTP_FROM,
        toaddrs=toaddrs,
        subject="",
    )

    if SETTINGS.SMTP_USER and SETTINGS.SMTP_PASS:  # pragma: no cover
        conf["credentials"] = (SETTINGS.SMTP_USER, SETTINGS.SMTP_PASS)
    if SETTINGS.SMTP_SECURE:
        conf["secure"] = tuple()

    return conf


LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "root": {
        "level": "INFO",
        "handlers": ["default"],
    },
    "loggers": {
        "gunicorn.error": {
            "level": "INFO",
            "handlers": ["app"],
            "propagate": True,
            "qualname": "gunicorn.error",
        },
        "gunicorn.access": {
            "level": "INFO",
            "handlers": ["app"],
            "propagate": True,
            "qualname": "gunicorn.access",
        },
        "worker": {
            "level": "INFO",
            "handlers": ["worker"],
            "propagate": True,
            "qualname": "gunicorn.access",
        },
    },
    "handlers": {
        "worker": {
            "class": "logging.FileHandler",
            "formatter": "worker",
            "filename": str(SETTINGS.get_logging_dir() / "worker.log"),
        },
        "app": {
            "class": "logging.FileHandler",
            "formatter": "app",
            "filename": str(SETTINGS.get_logging_dir() / "app.log"),
        },
        "default": {"class": "logging.StreamHandler", "formatter": "std", "stream": "ext://sys.stdout"},
    },
    "formatters": {
        "worker": {
            "format": "worker: %(asctime)s [%(process)d] [%(levelname)s] %(message)s",
            "datefmt": "[%Y-%m-%d %H:%M:%S %z]",
            "class": "logging.Formatter",
        },
        "app": {
            "format": "app: %(asctime)s [%(process)d] [%(levelname)s] %(message)s",
            "datefmt": "[%Y-%m-%d %H:%M:%S %z]",
            "class": "logging.Formatter",
        },
        "std": {"format": "%(asctime)s [%(process)d] [%(levelname)s] %(message)s"},
    },
}

config.dictConfig(LOGGING_CONFIG)
LOGGER = logging.getLogger("worker")

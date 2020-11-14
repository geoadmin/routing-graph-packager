from logging.handlers import SMTPHandler
import logging
from typing import List


#https://stackoverflow.com/a/9236722/2582935
class AppSmtpHandler(SMTPHandler):
    """The SMTP handler's extended class to write emails in case of events."""
    def getSubject(self, record: logging.LogRecord) -> str:
        """Alters the subject line of the emails."""
        subject = f'KADAS {record.levelname}: '
        if record.levelno == logging.ERROR:
            subject += f'Container ID {record.container_id} for router {record.router} failed'
        # Warning is only emitted in tasks.py, when the deletion fails
        elif record.levelno == logging.WARNING:
            subject += f"{record.user}'s job {record.job_id} was stopped and deleted"
        elif record.levelno == logging.INFO:
            subject += f'Job {record.job_id} by {record.user}'
        else:
            raise NotImplemented(f"Logger level {record.levelno} is not implemented for this handler.")

        return subject

    def emit(self, record):
        """Can be used to limit the emails sent out."""
        super().emit(record)


def get_smtp_details(config, toaddrs):
    """
    Dynamically create the config for the SMTP logger. Sort of assumes a valid
    App config to be passed.

    :param dict config: The App config ideally or any dict having the appropriate keys.
    :param List[str] toaddrs: The recipients' email addresses.
    # :param bool to_admin: Whether the email(s) should be sent to the DB Admin or not.

    :returns: complete SMTP configuration
    :rtype: dict
    """
    # if to_admin:
    #     add_email = config['ADMIN_EMAIL']
    #     if add_email not in toaddrs:
    #         toaddrs.append(config['ADMIN_EMAIL'])

    conf = dict(
        mailhost=(config['SMTP_HOST'], config['SMTP_PORT']),
        fromaddr=config['SMTP_FROM'],
        toaddrs=toaddrs,
        subject=''
    )

    if config['SMTP_USER'] and config['SMTP_PASS']:  # pragma: no cover
        conf['credentials'] = (config['SMTP_USER'], config['SMTP_PASS'])
    if config['SMTP_SECURE']:
        conf['secure'] = tuple()

    return conf

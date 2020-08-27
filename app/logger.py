from logging.handlers import SMTPHandler
import logging
from typing import List


#https://stackoverflow.com/a/9236722/2582935
class AppSmtpHandler(SMTPHandler):
    """The SMTP handler's extended class to write emails in case of events."""
    def getSubject(self, record: logging.LogRecord) -> str:
        """Alters the subject line of the emails."""
        subject = f'KADAS {record.levelname}: '
        if record.levelno > logging.INFO:
            subject += f'Container ID {record.container_id} für Router {record.router}'
        else:
            subject += 'Erfolg'

        return subject

    def emit(self, record):
        """Can be used to limit the emails sent out."""
        super().emit(record)


def get_smtp_details(config, toaddrs, to_admin=True):
    """
    Dynamically create the config for the SMTP logger. Sort of assumes a valid
    App config to be passed.

    :param dict config: The App config ideally or any dict having the appropriate keys.
    :param List[str] toaddrs: The recipient's email addresses.
    :param bool to_admin: Whether the email(s) should be sent to the DB Admin or not.

    :returns: complete SMTP configuration
    :rtype: dict
    """
    if to_admin:
        add_email = config['ADMIN_EMAIL']
        if add_email not in toaddrs:
            toaddrs.append(config['ADMIN_EMAIL'])

    conf = dict(
        mailhost=(config['SMTP_HOST'], config['SMTP_PORT']),
        fromaddr=config['SMTP_FROM'],
        toaddrs=toaddrs,
        subject=''
    )

    if config['SMTP_USER'] and config['SMTP_PASS']:
        conf['credentials'] = (config['SMTP_USER'], config['SMTP_PASS'])
    if config['SMTP_SECURE']:
        conf['secure'] = tuple()

    return conf

from logging.handlers import SMTPHandler
import logging


#https://stackoverflow.com/a/9236722/2582935
class AppSmtpHandler(SMTPHandler):
    def getSubject(self, record: logging.LogRecord) -> str:
        subject = f'KADAS {record.levelname}: '
        if record.levelno > logging.INFO:
            subject += f'Container ID {record.container_id} für Router {record.router}'
        else:
            subject += 'Erfolg'

        return subject

    def emit(self, record):
        super().emit(record)


def get_smtp_details(config, toaddrs, to_admin=True):
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

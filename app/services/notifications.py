import logging
import smtplib
from email.message import EmailMessage

from app.config import get_settings

log = logging.getLogger("orbitly.notifications")


def send_email(to: str, subject: str, body: str) -> None:
    settings = get_settings()
    msg = EmailMessage()
    msg["From"] = settings.mail_from
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as smtp:
        smtp.send_message(msg)
    log.info("sent '%s' to %s", subject, to)

"""Alert dispatchers — sends webhook or email notifications."""

import json
import logging
import smtplib
from email.message import EmailMessage
from typing import Optional

import urllib.request
import urllib.error

from cronwatch.config import AlertConfig

logger = logging.getLogger(__name__)


def send_webhook(url: str, payload: dict) -> bool:
    """POST a JSON payload to a webhook URL. Returns True on success."""
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            logger.info("Webhook delivered: HTTP %s", resp.status)
            return True
    except urllib.error.URLError as exc:
        logger.error("Webhook failed: %s", exc)
        return False


def send_email(config: AlertConfig, subject: str, body: str) -> bool:
    """Send an alert email using the SMTP settings in AlertConfig."""
    if not config.email_to or not config.smtp_host:
        logger.warning("Email alert skipped — missing email_to or smtp_host.")
        return False

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = config.email_from or "cronwatch@localhost"
    msg["To"] = ", ".join(config.email_to)
    msg.set_content(body)

    try:
        with smtplib.SMTP(config.smtp_host, config.smtp_port or 25, timeout=10) as smtp:
            if config.smtp_username and config.smtp_password:
                smtp.login(config.smtp_username, config.smtp_password)
            smtp.send_message(msg)
        logger.info("Email alert sent to %s", config.email_to)
        return True
    except smtplib.SMTPException as exc:
        logger.error("Email alert failed: %s", exc)
        return False


def dispatch_alert(config: AlertConfig, subject: str, body: str) -> None:
    """Dispatch an alert via all configured channels."""
    if config.webhook_url:
        send_webhook(config.webhook_url, {"subject": subject, "body": body})
    if config.email_to:
        send_email(config, subject, body)

"""Build an AlertChain from config and standard handler factories."""
from __future__ import annotations

from typing import Callable, Optional

from cronwatch.alert_chain import AlertChain, AlertHandler
from cronwatch.alerts import dispatch_alert
from cronwatch.config import AlertConfig
from cronwatch.history import HistoryEntry


def _webhook_handler(url: str) -> AlertHandler:
    """Return a handler that POSTs to *url* and returns True on success."""
    def _send(entry: HistoryEntry) -> bool:
        from cronwatch.alerts import send_webhook  # local import to avoid cycles
        return send_webhook(url, entry)
    return _send


def _email_handler(address: str) -> AlertHandler:
    """Return a handler that sends an email and returns True on success."""
    def _send(entry: HistoryEntry) -> bool:
        from cronwatch.alerts import send_email
        return send_email(address, entry)
    return _send


def _dispatch_handler(alert_config: AlertConfig) -> AlertHandler:
    """Wrap dispatch_alert as a chain-compatible handler."""
    def _send(entry: HistoryEntry) -> bool:
        dispatch_alert(alert_config, entry)
        return True
    return _send


def build_chain(
    alert_config: AlertConfig,
    extra_handler: Optional[AlertHandler] = None,
) -> AlertChain:
    """Construct an AlertChain from *alert_config*.

    Handlers are added in order:
    1. webhook (if configured)
    2. email (if configured)
    3. dispatch fallback
    4. any *extra_handler* provided by the caller
    """
    chain = AlertChain()

    if getattr(alert_config, "webhook_url", None):
        chain.add(_webhook_handler(alert_config.webhook_url))

    if getattr(alert_config, "email", None):
        chain.add(_email_handler(alert_config.email))

    chain.add(_dispatch_handler(alert_config))

    if extra_handler is not None:
        chain.add(extra_handler)

    return chain

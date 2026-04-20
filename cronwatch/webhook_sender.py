"""High-level webhook dispatch using webhook_template."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Callable

import urllib.request
import urllib.error
import json

from cronwatch.history import HistoryEntry
from cronwatch.webhook_template import build_payload

log = logging.getLogger(__name__)


@dataclass
class WebhookConfig:
    url: str
    method: str = "POST"
    headers: dict[str, str] = field(default_factory=lambda: {"Content-Type": "application/json"})
    template: str | None = None
    timeout: int = 10


@dataclass
class SendResult:
    ok: bool
    status_code: int | None = None
    error: str | None = None

    def __bool__(self) -> bool:
        return self.ok


def send_webhook_payload(
    entry: HistoryEntry,
    cfg: WebhookConfig,
    *,
    _requester: Callable | None = None,
) -> SendResult:
    """Render the payload from *entry* and POST it to ``cfg.url``.

    *_requester* is an optional injection point for testing; it receives
    ``(url, data_bytes, headers, method, timeout)`` and must return an object
    with a ``.status`` attribute.
    """
    payload_str = build_payload(entry, template_str=cfg.template)
    data = payload_str.encode()

    if _requester is not None:
        try:
            resp = _requester(cfg.url, data, cfg.headers, cfg.method, cfg.timeout)
            return SendResult(ok=200 <= resp.status < 300, status_code=resp.status)
        except Exception as exc:  # noqa: BLE001
            log.error("Webhook send failed: %s", exc)
            return SendResult(ok=False, error=str(exc))

    req = urllib.request.Request(
        cfg.url,
        data=data,
        headers=cfg.headers,
        method=cfg.method,
    )
    try:
        with urllib.request.urlopen(req, timeout=cfg.timeout) as resp:
            return SendResult(ok=True, status_code=resp.status)
    except urllib.error.HTTPError as exc:
        log.error("Webhook HTTP error %s for %s", exc.code, cfg.url)
        return SendResult(ok=False, status_code=exc.code, error=str(exc))
    except Exception as exc:  # noqa: BLE001
        log.error("Webhook send failed: %s", exc)
        return SendResult(ok=False, error=str(exc))

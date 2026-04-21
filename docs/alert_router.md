# Alert Router

The `alert_router` module decides **which notification channel** to use for each
failing job based on configurable routing rules.

## Overview

When cronwatch detects a problem it needs to decide whether to send a webhook,
an email, both, or nothing at all.  `AlertRouter` evaluates an ordered list of
`RouteRule` objects and returns the first matching channel.

## RouteRule

```python
RouteRule(
    tags=["critical"],   # job must carry at least one of these tags
    min_failures=1,       # failure_count must be >= this value
    channel="both",       # "webhook" | "email" | "both" | "none"
    label="crit",         # human-readable name for logging
)
```

| Field | Default | Description |
|---|---|---|
| `tags` | `[]` | Tag filter; empty list matches any entry |
| `min_failures` | `1` | Minimum failure count to trigger rule |
| `channel` | `"webhook"` | Destination channel |
| `label` | `""` | Optional human-readable rule name |

## AlertRouter

```python
router = AlertRouter(rules=[rule1, rule2], default_channel="webhook")
channel = router.route(entry)        # str
suppressed = router.should_suppress(entry)  # bool
```

Rules are evaluated in order; the first match wins.  If no rule matches the
`default_channel` is returned.

Setting `channel="none"` on a rule suppresses alerts for matching entries.
`should_suppress()` is a convenience wrapper that returns `True` when the
resolved channel is `"none"`.

## build_router helper

```python
from cronwatch.alert_router import build_router

router = build_router(alert_cfg, rules=[
    {"tags": ["db"], "min_failures": 2, "channel": "email"},
])
```

The `default_channel` is inferred from `AlertConfig`: `"webhook"` when a
webhook URL is configured, otherwise `"email"`.

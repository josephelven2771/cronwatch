# Alert Throttle

`cronwatch.alert_throttle` limits how many alerts can be fired for a single
job within a configurable rolling time window. This prevents alert storms when
a job fails repeatedly in a short period.

## Classes

### `ThrottlePolicy`

| Field | Type | Default | Description |
|---|---|---|---|
| `max_alerts` | `int` | `5` | Maximum alerts allowed per window |
| `window_seconds` | `int` | `3600` | Rolling window length in seconds |

### `ThrottleResult`

Returned by `AlertThrottle.check()`. Truthy when the alert is **allowed**.

| Field | Description |
|---|---|
| `allowed` | `True` if the alert may be sent |
| `job_name` | Job the check was performed for |
| `sent_in_window` | Alerts already sent within the current window |
| `max_alerts` | Configured limit |
| `reason` | Human-readable explanation when throttled |

### `AlertThrottle`

Stateful throttle tracker. Holds per-job timestamps in memory.

```python
from cronwatch.alert_throttle import AlertThrottle, ThrottlePolicy

policy = ThrottlePolicy(max_alerts=3, window_seconds=300)
throttle = AlertThrottle(policy)

result = throttle.check("nightly-backup")
if result:
    send_alert(...)          # your alert logic
    throttle.record("nightly-backup")
else:
    print(result.reason)     # "throttled: 3/3 alerts in window"
```

## Methods

- **`check(job_name, now=None) -> ThrottleResult`** — Check whether an alert
  is permitted. Prunes expired timestamps before evaluating.
- **`record(job_name, now=None) -> None`** — Call after successfully sending
  an alert to register the timestamp.
- **`reset(job_name) -> None`** — Clear all throttle state for a job (useful
  after a job recovers).

## Integration

`AlertThrottle` is designed to sit between the alert decision layer and the
actual send call, complementing `Notifier` (cooldown between repeated alerts)
and `RateLimiter` (global request-rate caps).

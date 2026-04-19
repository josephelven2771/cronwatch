# Notifier

The `Notifier` class wraps `dispatch_alert` with **rate-limiting** and **repeat capping** so that a flapping cron job does not flood your webhook or inbox.

## Usage

```python
from cronwatch.config import AlertConfig
from cronwatch.notifier import Notifier

alert_cfg = AlertConfig(webhook_url="https://hooks.slack.com/...")
notifier = Notifier(alert_cfg, cooldown_seconds=3600, max_repeats=5)

# Inside your monitoring loop:
if job_is_failing:
    notifier.notify(job_name, f"{job_name} failed", details)
else:
    notifier.reset(job_name)  # clears state on recovery
```

## Parameters

| Parameter | Default | Description |
|---|---|---|
| `alert_config` | required | `AlertConfig` instance (webhook / email) |
| `cooldown_seconds` | `3600` | Minimum seconds between alerts for the same job |
| `max_repeats` | `None` | Maximum total alerts per job (unlimited if `None`) |

## Behaviour

- **First failure** — alert sent immediately.
- **Repeated failures within cooldown** — suppressed.
- **After cooldown elapses** — next alert is sent.
- **`max_repeats` reached** — no further alerts until `reset()` is called.
- **Job recovers** — call `reset(job_name)` to clear counters so fresh failures alert again.

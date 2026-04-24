# Alert Suppressor

`cronwatch.alert_suppressor` provides a unified decision point that combines
three independent suppression mechanisms into a single `check()` call.

## Why

Without coordination, alerts can fire repeatedly for the same issue:
- A job fails every minute but alerts should only fire every 5 minutes (cooldown).
- An on-call rotation is sleeping and has silenced a job until morning (silencer).
- Two monitors both detect the same failure and would double-alert (deduplicator).

`AlertSuppressor` wraps all three and short-circuits on the first match.

## Usage

```python
from cronwatch.alert_suppressor import AlertSuppressor
from cronwatch.silencer import Silencer
from cronwatch.cooldown import CooldownTracker
from cronwatch.deduplicator import Deduplicator

suppressor = AlertSuppressor(
    silencer=Silencer(),
    cooldown=CooldownTracker(window_seconds=300),
    deduplicator=Deduplicator(window_seconds=60),
)

result = suppressor.check("backup", "exit code 1")
if result:
    send_alert(...)
    suppressor.record("backup", "exit code 1")
```

## API

### `AlertSuppressor`

| Field | Type | Description |
|---|---|---|
| `silencer` | `Silencer` | Active silence windows |
| `cooldown` | `CooldownTracker` | Per-job alert rate limiting |
| `deduplicator` | `Deduplicator` | Fingerprint-based dedup |

#### `check(job_name, message, now=None) -> SuppressionResult`

Returns a `SuppressionResult`. Evaluation order:
1. **silenced** — job matches an active silence window
2. **cooldown** — alert was sent too recently
3. **duplicate** — identical message fingerprint within window
4. **allowed** — none of the above

#### `record(job_name, message, now=None) -> None`

Call after successfully dispatching an alert to register the event with
both the cooldown tracker and the deduplicator.

#### `suppressed_count -> int`

Running total of suppressed checks since the instance was created.

### `SuppressionResult`

| Field | Type |
|---|---|
| `allowed` | `bool` |
| `reason` | `str` — `'allowed'`, `'silenced'`, `'cooldown'`, `'duplicate'` |

`bool(result)` is `True` only when `allowed` is `True`.

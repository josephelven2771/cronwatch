# AlertBatcher

`cronwatch.alert_batcher` provides a time-windowed accumulator that collects
`HistoryEntry` objects and flushes them as a single `AlertBatch` once the
configured window expires.

This prevents alert storms by grouping many rapid failures into one
notification rather than sending a separate message for every event.

---

## Classes

### `AlertBatch`

A dataclass that holds the entries collected during one flush window.

| Attribute / Property | Type | Description |
|----------------------|------|-------------|
| `entries` | `list[HistoryEntry]` | Accumulated job-run records |
| `flushed_at` | `float \| None` | Monotonic timestamp of the flush |
| `size` | `int` | Number of entries in the batch |
| `failure_count` | `int` | How many entries are failures |
| `summary()` | `str` | Human-readable one-liner |

### `AlertBatcher`

```python
AlertBatcher(
    window_seconds: float,
    on_flush: Callable[[AlertBatch], None],
    *,
    _clock: Callable[[], float] = time.monotonic,
)
```

| Method | Returns | Description |
|--------|---------|-------------|
| `add(entry)` | `None` | Append an entry; auto-flushes if the window has expired |
| `flush()` | `AlertBatch` | Immediately flush and reset; no-op (no callback) if batch is empty |
| `pending()` | `int` | Number of entries waiting to be flushed |

---

## Usage

```python
from cronwatch.alert_batcher import AlertBatcher
from cronwatch.alerts import dispatch_alert

def _send(batch):
    dispatch_alert(subject="Batch alert", body=batch.summary())

batcher = AlertBatcher(window_seconds=60, on_flush=_send)

# Called from your monitoring loop:
batcher.add(entry)
```

> **Tip:** Call `batcher.flush()` at shutdown to ensure the final partial
> batch is delivered.

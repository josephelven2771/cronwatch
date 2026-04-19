# Retrier

The `retrier` module provides configurable retry logic for job commands that may fail transiently.

## Classes

### `RetryPolicy`

Defines how retries are performed.

| Field | Type | Default | Description |
|---|---|---|---|
| `max_attempts` | int | 3 | Maximum number of attempts |
| `delay_seconds` | float | 5.0 | Initial delay between attempts |
| `backoff_factor` | float | 2.0 | Multiplier applied to delay after each failure |
| `max_delay_seconds` | float | 60.0 | Upper bound on delay |

### `RetryResult`

Returned by `retry()`.

| Field | Type | Description |
|---|---|---|
| `succeeded` | bool | Whether any attempt succeeded |
| `attempts` | int | Total attempts made |
| `last_error` | str or None | Output from the final failed attempt |
| `outputs` | list[str] | Collected output from every attempt |

## Functions

### `retry(fn, policy) -> RetryResult`

Calls `fn()` repeatedly according to `policy`. `fn` must return `(success: bool, output: str)`.

## Example

```python
from cronwatch.retrier import RetryPolicy, retry

policy = RetryPolicy(max_attempts=3, delay_seconds=2.0)

def run():
    ok = do_work()
    return ok, "done" if ok else "failed"

result = retry(run, policy)
if not result.succeeded:
    print(f"All {result.attempts} attempts failed: {result.last_error}")
```

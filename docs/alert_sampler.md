# alert_sampler

Probabilistic sampling for alert volume control.

When a large number of jobs fail simultaneously, `AlertSampler` prevents
notification floods by randomly allowing only a configured fraction of
alerts to proceed to the delivery stage.

## Classes

### `SamplePolicy`

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `rate` | `float` | `1.0` | Fraction of alerts to pass through (`0.0`–`1.0`). |
| `threshold` | `int` | `0` | Minimum number of entries before sampling is applied. |
| `seed` | `int \| None` | `None` | Optional RNG seed for deterministic tests. |

Raises `ValueError` if `rate` is outside `[0, 1]` or `threshold` is negative.

### `SampleResult`

Returned for every entry processed by `AlertSampler.sample()`.

| Field | Type | Description |
|-------|------|-------------|
| `entry` | `HistoryEntry` | The original entry. |
| `allowed` | `bool` | Whether this entry passed the sampler. |
| `rate` | `float` | The effective sampling rate applied. |

`bool(result)` returns `True` when the entry was allowed through.

### `AlertSampler`

```python
sampler = AlertSampler(policy=SamplePolicy(rate=0.25, threshold=5))
```

#### `sample(entries) -> list[SampleResult]`

Returns one `SampleResult` per entry.  Sampling is only applied when
`len(entries) > policy.threshold`; otherwise every entry is allowed.

#### `filter(entries) -> list[HistoryEntry]`

Convenience wrapper that returns only the entries whose `SampleResult` is
`True`.

## Example

```python
from cronwatch.alert_sampler import AlertSampler, SamplePolicy

policy = SamplePolicy(rate=0.3, threshold=10)
sampler = AlertSampler(policy=policy)

# entries is a list[HistoryEntry] gathered during a monitor check
passing = sampler.filter(entries)
for entry in passing:
    dispatch_alert(entry)
```

With `threshold=10`, all entries pass when ten or fewer failures are
detected.  Above that limit each entry is independently accepted with 30 %
probability, capping the expected number of outgoing alerts at roughly
`0.3 × N`.

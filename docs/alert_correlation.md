# Alert Correlation

The `alert_correlation` module groups related failing alerts into **correlated events** so that operators see a single root-cause summary instead of a flood of individual notifications.

## Overview

| Class | Purpose |
|---|---|
| `CorrelatedEvent` | Immutable record of grouped alerts sharing a common key |
| `AlertCorrelator` | Buckets `HistoryEntry` objects by a derived correlation key |
| `AlertCorrelationRunner` | Orchestrates correlation across all configured jobs |

## How correlation keys work

By default (`group_by_prefix=True`) the correlator strips the last `_`-separated segment from a job name:

```
backup_daily   → backup
backup_weekly  → backup
report_daily   → report
nightly        → nightly   (no underscore — key equals full name)
```

Set `group_by_prefix=False` to treat every job name as its own independent key.

## Quick start

```python
from cronwatch.alert_correlation_runner import AlertCorrelationRunner

runner = AlertCorrelationRunner(config, store, limit=100)
events = runner.run()

for event in events:
    print(event.summary)
    # [backup] 3 events across [backup_daily, backup_weekly] (3 failures)
```

## CorrelatedEvent fields

| Field | Type | Description |
|---|---|---|
| `correlation_id` | `str` | Derived group key |
| `job_names` | `List[str]` | All job names in the group |
| `entries` | `List[HistoryEntry]` | Raw history entries |
| `first_seen` | `datetime` | Earliest `started_at` in the group |
| `last_seen` | `datetime` | Latest `started_at` in the group |
| `tags` | `List[str]` | Union of tags from all entries |

## AlertCorrelationRunner

```python
runner = AlertCorrelationRunner(
    config,
    store,
    limit=50,          # max entries per job to inspect
    group_by_prefix=True,
)
events   = runner.run()         # all correlated failure groups
corr     = runner.correlated    # only multi-job groups
lines    = runner.summary_lines()
```

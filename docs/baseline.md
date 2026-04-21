# Baseline

The `baseline` module tracks per-job historical performance metrics and detects anomalous runs.

## Overview

As cron jobs run over time, `Baseline` accumulates duration and failure data for each job. This allows cronwatch to flag runs that deviate significantly from historical norms.

## Classes

### `BaselineStats`

Holds aggregated statistics for a single job.

| Field | Type | Description |
|---|---|---|
| `job_name` | `str` | Identifier for the job |
| `sample_count` | `int` | Number of recorded runs |
| `total_duration` | `float` | Sum of all run durations (seconds) |
| `failure_count` | `int` | Number of failed runs |

**Properties**
- `avg_duration` – mean duration across all samples, or `None` if no samples.
- `failure_rate` – fraction of runs that failed (`0.0`–`1.0`).

### `BaselineDeviation`

Result of comparing a current run against the baseline.

| Field | Description |
|---|---|
| `avg_duration` | Historical average (may be `None`) |
| `current_duration` | Duration of the run being evaluated |
| `threshold_multiplier` | How many times the average before flagging |
| `is_anomalous` | `True` when `current > avg * threshold_multiplier` |

### `Baseline`

Persistent store for baseline statistics backed by a JSON file.

```python
from pathlib import Path
from cronwatch.baseline import Baseline

baseline = Baseline(Path(".cronwatch/baseline.json"))

# Record a completed run
baseline.record("db-backup", duration=42.3, succeeded=True)

# Check for anomalous duration
deviation = baseline.check_deviation("db-backup", current_duration=120.0)
if deviation.is_anomalous:
    print(f"db-backup took {deviation.current_duration}s vs avg {deviation.avg_duration:.1f}s")
```

## Integration

Call `baseline.record()` at the end of each job run (e.g., from `runner.py`). Use `check_deviation()` inside the monitor or alert pipeline to surface slow jobs before they become failures.

# Anomaly Detection

The `anomaly` module flags cron job runs whose duration deviates significantly
from the historical baseline using a simple **z-score** test.

## How it works

1. After each run the `Baseline` module accumulates mean and standard deviation
   for every job's duration.
2. `detect_duration_anomaly()` computes the z-score of the latest run against
   those statistics.
3. When `|z| ≥ z_threshold` (default **3.0**) the run is flagged as anomalous.

## Quick start

```python
from cronwatch.anomaly import detect_duration_anomaly
from cronwatch.baseline import Baseline

baseline = Baseline(path=".cronwatch/baseline.json")
stats = baseline.stats_for("nightly-backup")
result = detect_duration_anomaly("nightly-backup", actual_duration=420.0, stats=stats)

if result:
    print(f"Anomaly detected: {result.reason}")
```

## AnomalyChecker

`AnomalyChecker` wraps the low-level function and integrates with the full
stack (`CronwatchConfig`, `HistoryStore`, `Baseline`).

```python
from cronwatch.anomaly_checker import AnomalyChecker

checker = AnomalyChecker(config, store, baseline)
for anomaly in checker.anomalies():
    print(anomaly.job_name, anomaly.reason)
```

## AnomalyResult fields

| Field | Type | Description |
|---|---|---|
| `job_name` | `str` | Name of the job |
| `is_anomaly` | `bool` | `True` when flagged |
| `reason` | `str \| None` | Human-readable explanation |
| `actual_duration` | `float \| None` | Duration of the run in seconds |
| `expected_duration` | `float \| None` | Baseline average |
| `z_score` | `float \| None` | Computed z-score |

## Configuration

Pass a custom `z_threshold` to `AnomalyChecker` or `detect_duration_anomaly`
to tune sensitivity:

```python
checker = AnomalyChecker(config, store, baseline, z_threshold=2.5)
```

A lower threshold produces more alerts; the default of **3.0** targets
clear outliers while avoiding noise on small datasets.

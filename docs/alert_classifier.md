# Alert Classifier

The `alert_classifier` module assigns a **severity level** to each job alert
based on multiple health signals, allowing downstream components (routers,
batchers, notifiers) to make priority-aware decisions.

## Severity Levels

| Level      | Meaning                                      |
|------------|----------------------------------------------|
| `LOW`      | Job is healthy — no action needed            |
| `MEDIUM`   | Minor concern, worth watching                |
| `HIGH`     | Significant problem, alert recommended       |
| `CRITICAL` | Severe, multi-signal failure — act now       |

## Usage

```python
from cronwatch.alert_classifier import classify, Severity

result = classify(
    job_name="backup",
    entry=last_entry,
    consecutive_failures=6,
    failure_rate=0.8,
)

if result:          # True when HIGH or CRITICAL
    print(result)   # [CRITICAL] backup: job failed; 6 consecutive failures; failure rate 80%
```

## AlertClassifierRunner

For bulk classification across all configured jobs:

```python
runner = AlertClassifierRunner(config, store, baseline, checkpoints)
runner.run()

for r in runner.actionable():
    print(r)
```

## Scoring

Internal scoring is additive:

- Job failed → +2
- 2–4 consecutive failures → +1; ≥5 → +3
- Failure rate 40–74 % → +1; ≥75 % → +3

Total score maps to severity: 0 → LOW, 1–2 → MEDIUM, 3–4 → HIGH, ≥5 → CRITICAL.

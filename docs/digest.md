# Digest Module

The `cronwatch.digest` module aggregates the status of all configured jobs
into a single **Digest** object suitable for periodic summary reports.

## Key Types

### `DigestEntry`
Represents the status of one job:
- `job_name` – name from config
- `status` – `"healthy"`, `"missed"`, or `"failed"`
- `last_run` – UTC datetime of the last recorded finish, or `None`
- `summary` – human-readable one-liner (from `Reporter.summary_line`)

### `Digest`
Top-level container:
- `generated_at` – UTC timestamp of digest creation
- `entries` – list of `DigestEntry`
- `healthy_count` / `problem_count` – convenience properties
- `to_dict()` – serialisable dict for webhook payloads or logging

## Usage

```python
from cronwatch.digest import build_digest
from cronwatch.reporter import Reporter
from cronwatch.history import HistoryStore

store = HistoryStore(path="/var/lib/cronwatch/history.json")
reporter = Reporter(config=cfg, store=store)
digest = build_digest(cfg, reporter)
print(digest.to_dict())
```

## Integration

`build_digest` is called by the `Monitor` during scheduled digest runs and
the resulting dict can be forwarded to `dispatch_alert` as the payload body.

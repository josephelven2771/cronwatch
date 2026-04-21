# Snapshot

The **snapshot** feature captures a point-in-time view of all monitored job
statuses and persists it to disk. This allows cronwatch to detect status changes
between runs and emit targeted alerts only when something actually changes.

## Modules

### `cronwatch/snapshot.py`

Defines the data model:

- **`JobSnapshot`** – per-job data: last run time, exit code, duration, success/failure counts.
- **`Snapshot`** – container for all `JobSnapshot` entries, stamped with `taken_at`.
- **`save_snapshot(snapshot, path)`** – serialises a snapshot to a JSON file.
- **`load_snapshot(path)`** – deserialises a snapshot from disk; returns `None` if missing.

### `cronwatch/snapshot_builder.py`

Builds and compares snapshots:

- **`build_snapshot(config, store)`** – iterates configured jobs, reads their
  history, and produces a fresh `Snapshot`.
- **`diff_snapshots(before, after)`** – returns a dict of job names whose status
  changed between two snapshots (different exit code or new last-run time).

## Usage

```python
from cronwatch.snapshot import load_snapshot, save_snapshot
from cronwatch.snapshot_builder import build_snapshot, diff_snapshots

prev = load_snapshot(state_path)          # may be None on first run
current = build_snapshot(config, store)

if prev:
    changes = diff_snapshots(prev, current)
    for job_name, delta in changes.items():
        print(f"{job_name} changed: {delta}")

save_snapshot(current, state_path)
```

## File format

Snapshots are stored as pretty-printed JSON:

```json
{
  "taken_at": "2024-06-01T12:00:00+00:00",
  "jobs": {
    "backup": {
      "job_name": "backup",
      "last_run": "2024-06-01T11:55:00+00:00",
      "last_exit_code": 0,
      "last_duration": 12.4,
      "success_count": 42,
      "failure_count": 1
    }
  }
}
```

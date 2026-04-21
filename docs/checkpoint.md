# Checkpoint

The **checkpoint** module provides persistent per-job execution state that
survives process restarts. It is designed to complement the append-only
`HistoryStore` by maintaining a compact, mutable summary of each job's
current health.

## Core types

### `JobCheckpoint`

Holds the current state for a single job:

| Field | Type | Description |
|---|---|---|
| `job_name` | `str` | Unique job identifier |
| `last_success` | `datetime \| None` | UTC timestamp of most recent success |
| `last_failure` | `datetime \| None` | UTC timestamp of most recent failure |
| `consecutive_failures` | `int` | Failures since the last success |
| `total_runs` | `int` | Lifetime run count |

```python
cp = JobCheckpoint(job_name="nightly-backup")
cp.record_success()   # resets consecutive_failures
cp.record_failure()   # increments consecutive_failures
```

### `CheckpointStore`

A thin JSON-backed dictionary of `JobCheckpoint` objects.

```python
store = CheckpointStore.load(Path(".cronwatch/checkpoints.json"))
cp = store.get_or_create("etl")
cp.record_failure()
store.save()
```

## High-level interface

### `CheckpointManager`

Builds on top of `CheckpointStore` and exposes convenience methods:

```python
manager = CheckpointManager.from_path(Path(".cronwatch/checkpoints.json"))

manager.record_success("etl")
manager.record_failure("etl")

print(manager.consecutive_failures("etl"))  # 1

bad_jobs = manager.jobs_with_consecutive_failures(min_failures=3)
```

## Persistence

Checkpoints are stored as a single JSON file (one object per job). The file
is written atomically via `Path.write_text` after every mutation so that a
crash cannot leave the store in a partially-written state.

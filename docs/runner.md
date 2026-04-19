# Runner

The `cronwatch.runner` module executes a cron job's shell command in a subprocess and records the outcome to history.

## API

### `run_job(job, store, tracker=None, timeout=None) -> RunResult`

Runs `job.command` via the shell and:

1. Marks the run as started in `JobTracker`.
2. Captures stdout / stderr.
3. Marks the run as finished (success or failure).
4. Persists the result to `HistoryStore`.
5. Returns a `RunResult` dataclass.

**Parameters**

| Name | Type | Description |
|------|------|-------------|
| `job` | `JobConfig` | Job definition including `command` and `name`. |
| `store` | `HistoryStore` | Persistent history backend. |
| `tracker` | `JobTracker \| None` | In-memory run tracker; created automatically when `None`. |
| `timeout` | `int \| None` | Optional subprocess timeout in seconds. |

### `RunResult`

| Field | Type | Description |
|-------|------|-------------|
| `job_name` | `str` | Name of the job. |
| `exit_code` | `int` | Process exit code (`124` on timeout). |
| `stdout` | `str` | Captured standard output. |
| `stderr` | `str` | Captured standard error. |
| `duration_seconds` | `float` | Wall-clock execution time. |
| `succeeded` | `bool` | `True` when `exit_code == 0`. |

## Example

```python
from cronwatch.runner import run_job
from cronwatch.history import HistoryStore
from cronwatch.config import JobConfig

store = HistoryStore(path="/var/lib/cronwatch/history.json")
job = JobConfig(name="backup", command="/usr/local/bin/backup.sh", schedule="0 2 * * *")
result = run_job(job, store, timeout=3600)
if not result.succeeded:
    print(f"Job failed with exit code {result.exit_code}")
```

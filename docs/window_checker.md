# Window Checker

The `window_checker` module verifies that cron jobs ran **within an expected
time window** each day. This is useful when a job must execute during a
specific maintenance or low-traffic period.

## Configuration

Add `window_start` and `window_end` (24-hour `HH:MM` strings) to a job in
`cronwatch.yml`:

```yaml
jobs:
  - name: nightly-backup
    schedule: "0 3 * * *"
    window_start: "02:00"
    window_end: "04:00"
```

Jobs that do **not** define both fields are silently skipped by the checker.

## API

### `check_window(job, store, now=None) -> WindowResult`

Checks a single job against the current day's window.

| Field | Type | Description |
|---|---|---|
| `job_name` | `str` | Name of the job |
| `expected_start` | `datetime` | Window open time (UTC today) |
| `expected_end` | `datetime` | Window close time (UTC today) |
| `last_run` | `datetime \| None` | Most recent run start |
| `in_window` | `bool` | `True` when last run falls inside the window |
| `message` | `str` | Human-readable summary |

`bool(result)` returns `True` when the job is within its window.

### `WindowChecker`

Batch checker that iterates over all windowed jobs in a `CronwatchConfig`.

```python
from cronwatch.window_checker import WindowChecker

checker = WindowChecker(config=cfg, store=history_store)
results = checker.check_all()

for violation in checker.violations:
    print(violation.message)
```

#### Methods

- `check_all(now=None) -> List[WindowResult]` — run checks for every job
  that has `window_start` / `window_end` defined.
- `violations` — property returning only results where `in_window` is `False`.

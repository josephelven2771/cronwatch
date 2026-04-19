# History Pruner

The `cronwatch.pruner` module keeps the history store from growing without bound by removing old or excess entries.

## Functions

### `prune_by_age(store, job_name, max_age_days) -> int`

Removes all history entries for `job_name` whose `started_at` timestamp is older than `max_age_days`. Returns the number of entries removed.

```python
from cronwatch.history import HistoryStore
from cronwatch.pruner import prune_by_age

store = HistoryStore("/var/lib/cronwatch/history.json")
removed = prune_by_age(store, "nightly-backup", max_age_days=30)
print(f"Removed {removed} old entries.")
```

### `prune_by_count(store, job_name, max_entries) -> int`

Keeps only the `max_entries` most recent entries for `job_name`, discarding the rest. Returns the number of entries removed.

### `prune_all(store, max_age_days=None, max_entries=None) -> dict[str, int]`

Runs pruning across **all** jobs currently in the store. Both strategies can be combined — age pruning runs first, then count pruning.

```python
from cronwatch.pruner import prune_all

results = prune_all(store, max_age_days=90, max_entries=50)
for job, count in results.items():
    print(f"{job}: {count} entries pruned")
```

## Integration

Call `prune_all` from the CLI `check` command or a dedicated maintenance cron to keep storage usage predictable. Recommended defaults: 90-day age limit, 200 max entries per job.

# Filter

The `cronwatch.filter` module provides utilities for querying `HistoryEntry` records by job name, time range, and outcome.

## FilterCriteria

```python
@dataclass
class FilterCriteria:
    job_name: Optional[str] = None
    since: Optional[datetime] = None
    until: Optional[datetime] = None
    succeeded_only: bool = False
    failed_only: bool = False
    limit: Optional[int] = None
```

All fields are optional. Unset fields are ignored during filtering.

## Functions

### `filter_entries(entries, criteria) -> List[HistoryEntry]`

Filters an iterable of `HistoryEntry` objects against a `FilterCriteria` instance. Results are returned sorted chronologically by `started_at`. If `limit` is set, the *most recent* N entries are returned after sorting.

### `filter_by_job(entries, job_name) -> List[HistoryEntry]`

Convenience wrapper that returns all entries for a single named job.

### `filter_failures(entries) -> List[HistoryEntry]`

Convenience wrapper that returns only entries where `succeeded` is `False`.

## Example

```python
from cronwatch.filter import FilterCriteria, filter_entries
from cronwatch.history import HistoryStore
from datetime import datetime, timedelta

store = HistoryStore(".cronwatch_history.json")
all_entries = store.all()

recent_failures = filter_entries(
    all_entries,
    FilterCriteria(
        since=datetime.utcnow() - timedelta(hours=24),
        failed_only=True,
        limit=10,
    ),
)
```

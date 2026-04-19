# Tagger

The `tagger` module provides tag-based grouping and filtering of history entries.

## Overview

Jobs can be annotated with tags (e.g. `daily`, `storage`, `email`). The tagger
module lets you slice history entries by those tags.

## API

### `tag_entries(entries, tags) -> List[HistoryEntry]`

Returns only entries whose tag set overlaps with the provided `tags` list.
Passing an empty list returns all entries unchanged.

### `build_tag_index(entries) -> TagIndex`

Builds an inverted index from tag name to matching entries for fast lookup.

```python
idx = build_tag_index(store.all())
daily_entries = idx.get("daily")
```

### `group_by_tag(entries) -> Dict[str, List[HistoryEntry]]`

Groups entries by each of their tags. An entry with multiple tags appears
under each tag group.

### `TagIndex`

| Method | Description |
|---|---|
| `add(entry)` | Index a single entry |
| `get(tag)` | Retrieve entries for a tag |
| `all_tags()` | Sorted list of all known tags |

## Example

```python
from cronwatch.tagger import build_tag_index

idx = build_tag_index(history_store.all())
for entry in idx.get("critical"):
    print(entry.job_name, entry.exit_code)
```

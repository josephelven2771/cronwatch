# alert_enricher

The `alert_enricher` module attaches contextual metadata to alert entries
before they are dispatched.  This lets downstream handlers make smarter
decisions (e.g. escalate only after three consecutive failures, or include
the average duration in the webhook body).

## Classes

### `EnrichedEntry`

A thin wrapper around a `HistoryEntry` that carries extra fields:

| Field | Type | Description |
|---|---|---|
| `entry` | `HistoryEntry` | The original history record |
| `consecutive_failures` | `int` | How many back-to-back failures |
| `avg_duration` | `float \| None` | Baseline average duration (seconds) |
| `last_success_iso` | `str \| None` | ISO-8601 timestamp of last success |
| `extra` | `dict` | Arbitrary additional context |

Call `.to_dict()` to get a JSON-serialisable representation that includes
both the original entry fields and an `enrichment` sub-object.

### `AlertEnricher`

```python
enricher = AlertEnricher(store, baseline_store)
rich = enricher.enrich(entry)          # single entry
all_rich = enricher.enrich_all(entries)  # batch
```

### `AlertEnricherRunner`

Convenience pipeline step that enriches a batch, applies a
`min_consecutive_failures` filter, and optionally calls a send function.

```python
runner = AlertEnricherRunner(enricher, min_consecutive_failures=2)
runner.run(entries, send=my_send_fn)
for e in runner.actionable:
    print(e.job_name, e.consecutive_failures)
```

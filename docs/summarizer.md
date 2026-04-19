# Summarizer

The `summarizer` module converts a `Digest` into a human-readable `SummaryReport`.

## Usage

```python
from cronwatch.summarizer import build_summary

# Given a Digest built by the reporter/digest pipeline:
report = build_summary(digest)
print(report)  # prints formatted summary to stdout
```

## SummaryReport

| Field | Type | Description |
|-------|------|-------------|
| `total` | `int` | Total number of jobs in the digest |
| `healthy` | `int` | Number of healthy jobs |
| `problems` | `int` | Number of jobs with issues |
| `lines` | `List[str]` | Individual lines of the report |

`str(report)` returns all lines joined by newlines.

## Example Output

```
cronwatch report — 2/3 jobs healthy
----------------------------------------
  [✓] backup: last run 10m ago, exit 0
  [✗] nightly: overdue by 2h
  [✓] cleanup: last run 30m ago, exit 0
----------------------------------------
1 job(s) require attention.
```

## Functions

### `build_summary(digest: Digest) -> SummaryReport`

Builds a `SummaryReport` from the given `Digest`. Each job entry is formatted
with a status icon (`✓` healthy, `✗` problem) and its summary line.

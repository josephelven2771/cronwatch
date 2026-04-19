# Exporter

The `Exporter` module converts a `Digest` snapshot into human-readable or
machine-readable output and optionally persists it to disk.

## Supported Formats

| Format | Description |
|--------|-------------|
| `text` | Plain-text report suitable for emails or terminal output |
| `json` | Structured JSON, useful for downstream tooling or dashboards |

## Usage

```python
from cronwatch.exporter import Exporter

exporter = Exporter(fmt="text")
print(exporter.render(digest))

# Write to file
exporter.write(digest, "/var/log/cronwatch/report.txt")
```

## JSON Schema

The JSON output mirrors `Digest.to_dict()`:

```json
{
  "generated_at": "2024-06-01T12:00:00+00:00",
  "healthy_count": 3,
  "problem_count": 1,
  "entries": [
    {
      "job_name": "backup",
      "healthy": true,
      "last_run": "2024-06-01T11:45:00+00:00",
      "message": "last run succeeded"
    }
  ]
}
```

## CLI Integration

The `cmd_check` command in `cli.py` can accept `--format` and `--output` flags
that delegate to `Exporter` for report generation.

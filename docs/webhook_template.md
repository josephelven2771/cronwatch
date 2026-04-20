# Webhook Template

The `cronwatch.webhook_template` module lets you customise the JSON payload
sent to a webhook endpoint when a job succeeds or fails.

## Default payload

When no custom template is provided, the following JSON structure is sent:

```json
{
  "job": "<job_name>",
  "status": "success|failure",
  "exit_code": 0,
  "started_at": "2024-06-01T02:00:00+00:00",
  "finished_at": "2024-06-01T02:00:45+00:00",
  "duration_seconds": 45.0,
  "message": "Job 'backup' success."
}
```

## Custom templates

Pass any `string.Template`-compatible string to `build_payload`:

```python
from cronwatch.webhook_template import build_payload

tpl = '{"text": "${job_name} finished with status ${status}"}'
payload = build_payload(entry, template_str=tpl)
```

Available variables:

| Variable | Description |
|---|---|
| `job_name` | Name of the cron job |
| `status` | `success` or `failure` |
| `exit_code` | Process exit code (or `null`) |
| `started_at` | ISO-8601 start timestamp |
| `finished_at` | ISO-8601 finish timestamp |
| `duration_seconds` | Wall-clock duration in seconds |
| `message` | Human-readable summary |

## Dict payload

If your HTTP client accepts a dict, use `build_json_payload`:

```python
from cronwatch.webhook_template import build_json_payload

data = build_json_payload(entry)  # returns dict
requests.post(url, json=data)
```

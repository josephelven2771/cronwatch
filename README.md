cronwatch

A lightweight CLI monitor that alerts on missed or failing cron jobs via webhook or email.

---

## Installation

```bash
pip install cronwatch
```

Or install from source:

```bash
git clone https://github.com/yourname/cronwatch.git && cd cronwatch && pip install .
```

---

## Usage

Wrap any cron job command with `cronwatch` to monitor its execution:

```bash
cronwatch --name "daily-backup" --notify email run ./backup.sh
```

Configure alerts in `cronwatch.yml`:

```yaml
jobs:
  daily-backup:
    schedule: "0 2 * * *"
    notify:
      email: alerts@example.com
      webhook: https://hooks.slack.com/services/your/webhook/url
    timeout: 300
```

Check job status manually:

```bash
cronwatch status
cronwatch status --name "daily-backup"
```

Run a quick test alert to verify your notification settings:

```bash
cronwatch test-notify --email alerts@example.com
```

---

## Configuration

| Option | Description | Default |
|---|---|---|
| `schedule` | Cron expression for expected run time | required |
| `timeout` | Max allowed runtime in seconds | `3600` |
| `notify.email` | Alert recipient email address | — |
| `notify.webhook` | Webhook URL for Slack/Discord/etc. | — |

---

## License

MIT © 2024 [Your Name](https://github.com/yourname)
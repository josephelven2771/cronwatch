# Escalator

The `Escalator` class tracks consecutive failures per job and promotes alerts
to an *escalated* state once a configurable threshold is reached.

## Overview

Some cron failures are transient. Rather than paging on-call immediately, you
may want to wait until a job has failed **N times in a row** before treating
it as a real incident. `Escalator` implements this pattern.

## Configuration

```python
from cronwatch.escalator import Escalator, EscalationPolicy

policy = EscalationPolicy(
    threshold=3,          # failures before escalation
    cooldown_minutes=60,  # successful run must be this old before de-escalating
)
escalator = Escalator(policy)
```

## Usage

```python
result = escalator.record_failure("nightly-backup")
if result.escalated:
    send_pagerduty_alert(result)

# On a successful run:
escalator.record_success("nightly-backup")
```

## API

### `record_failure(job_name, now=None) -> EscalationResult`

Increment the consecutive-failure counter. Returns an `EscalationResult`
(truthy when escalated).

### `record_success(job_name, now=None) -> None`

Reset the counter **only** if the cooldown window has elapsed since escalation
began. This prevents a single lucky run from immediately silencing an incident.

### `is_escalated(job_name) -> bool`

Check current escalation state without recording an event.

### `reset(job_name) -> None`

Unconditionally clear all state for a job (useful in tests or manual ops).

## EscalationResult fields

| Field | Type | Description |
|---|---|---|
| `job_name` | `str` | Name of the job |
| `escalated` | `bool` | Whether currently escalated |
| `consecutive_failures` | `int` | Running failure count |
| `escalated_since` | `datetime \| None` | When escalation began |

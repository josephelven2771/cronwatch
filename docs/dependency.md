# Dependency Tracking

Cronwatch can model prerequisites between jobs so that a job is only
considered *ready* when all of its declared predecessors have completed
successfully.

## Configuration

Add a `depends_on` list to any job in `cronwatch.yml`:

```yaml
jobs:
  - name: extract
    schedule: "0 2 * * *"
    command: ./extract.sh

  - name: transform
    schedule: "30 2 * * *"
    command: ./transform.sh
    depends_on:
      - extract

  - name: load
    schedule: "0 3 * * *"
    command: ./load.sh
    depends_on:
      - transform
```

## DependencyGraph

Holds a directed graph of `job → prerequisite` edges.

| Method | Description |
|--------|-------------|
| `add(job, deps)` | Register prerequisites for a job |
| `dependencies_for(job)` | List direct prerequisites |
| `all_jobs()` | Set of every known job name |

## check_dependencies(graph, job_name, completed)

Returns a `DependencyResult`:

- `blocked_by` — prerequisites that exist but have not yet completed.
- `missing` — prerequisites that are not registered in the graph at all.
- `bool(result)` — `True` when the job is clear to run.

## DependencyChecker

High-level wrapper built from a `CronwatchConfig`.

```python
checker = DependencyChecker(config)
result = checker.check_job("load", completed={"extract", "transform"})
if result:
    print("load is ready")
else:
    print("blocked by:", result.blocked_by)
```

### topological_order

`DependencyChecker.execution_order()` returns jobs sorted so that every
prerequisite appears before the jobs that depend on it.  Returns `None`
if a cycle is detected.

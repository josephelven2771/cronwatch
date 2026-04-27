# Alert Chain

The **alert chain** module provides a sequential handler pipeline that tries
each alert handler in order and stops at the first success.

## Concepts

| Class / function | Purpose |
|---|---|
| `AlertChain` | Holds an ordered list of `AlertHandler` callables |
| `ChainResult` | Outcome of running the chain against a single entry |
| `build_chain` | Factory that wires up handlers from an `AlertConfig` |

## Usage

```python
from cronwatch.alert_chain import AlertChain
from cronwatch.alert_chain_builder import build_chain

# Build from config
chain = build_chain(alert_config)

# Run against a single history entry
result = chain.run(entry)
if result:
    print(f"Alerted via handler #{result.handler_index}")
else:
    print("All handlers failed:", result.errors)

# Run against multiple entries
results = chain.run_all(entries)
```

## Handler contract

An `AlertHandler` is any `Callable[[HistoryEntry], bool]`.  Return `True` to
signal success and stop the chain; return `False` or raise an exception to
fall through to the next handler.  Exceptions are caught, recorded in
`ChainResult.errors`, and do **not** propagate.

## Building a custom chain

```python
chain = AlertChain()
chain.add(my_slack_handler)
chain.add(my_pagerduty_handler)
```

Handlers are tried in insertion order.

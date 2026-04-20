"""Persist and load Silencer state to/from a JSON file."""

from __future__ import annotations

import json
from pathlib import Path

from cronwatch.silencer import Silencer


def save_silencer(silencer: Silencer, path: Path) -> None:
    """Serialise *silencer* to *path* as JSON."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(silencer.to_dict(), fh, indent=2)


def load_silencer(path: Path) -> Silencer:
    """Load a Silencer from *path*. Returns an empty Silencer if the file
    does not exist or is malformed.
    """
    path = Path(path)
    if not path.exists():
        return Silencer()
    try:
        with path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        return Silencer.from_dict(data)
    except (json.JSONDecodeError, KeyError, ValueError):
        return Silencer()

"""Export job status reports to various formats (JSON, plain text)."""
from __future__ import annotations

import json
from datetime import datetime
from typing import List

from cronwatch.digest import Digest, DigestEntry


def _fmt_time(dt: datetime | None) -> str:
    if dt is None:
        return "never"
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def entry_to_text(entry: DigestEntry) -> str:
    status = "OK" if entry.healthy else "PROBLEM"
    last = _fmt_time(entry.last_run)
    return f"[{status}] {entry.job_name}: last_run={last} message={entry.message}"


def digest_to_text(digest: Digest) -> str:
    lines = [
        f"cronwatch report — {_fmt_time(digest.generated_at)}",
        f"healthy: {digest.healthy_count}  problems: {digest.problem_count}",
        "-" * 50,
    ]
    for entry in digest.entries:
        lines.append(entry_to_text(entry))
    return "\n".join(lines)


def digest_to_json(digest: Digest) -> str:
    return json.dumps(digest.to_dict(), indent=2, default=str)


class Exporter:
    """Render a Digest to a chosen format and optionally write to a file."""

    FORMATS = ("text", "json")

    def __init__(self, fmt: str = "text") -> None:
        if fmt not in self.FORMATS:
            raise ValueError(f"Unknown format {fmt!r}; choose from {self.FORMATS}")
        self.fmt = fmt

    def render(self, digest: Digest) -> str:
        if self.fmt == "json":
            return digest_to_json(digest)
        return digest_to_text(digest)

    def write(self, digest: Digest, path: str) -> None:
        content = self.render(digest)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(content)
            if not content.endswith("\n"):
                fh.write("\n")

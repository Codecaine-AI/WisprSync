from __future__ import annotations

from pathlib import Path
from typing import Any

from wisprsync.source.history import history_count


def discover_sources() -> list[dict[str, Any]]:
    candidates = [
        Path("~/Library/Application Support/Wispr Flow/flow.sqlite").expanduser(),
        Path("~/Library/Application Support/Flow/flow.sqlite").expanduser(),
    ]
    results: list[dict[str, Any]] = []
    seen: set[Path] = set()
    for candidate in candidates:
        try:
            resolved = candidate.resolve()
        except FileNotFoundError:
            resolved = candidate
        if resolved in seen:
            continue
        seen.add(resolved)
        if not candidate.exists():
            continue
        count = history_count(candidate)
        if count is None:
            continue
        results.append({"path": str(candidate), "history_rows": count})
    results.sort(key=lambda item: item["history_rows"], reverse=True)
    return results

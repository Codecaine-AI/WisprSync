from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def parse_json_field(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (dict, list, int, float, bool)):
        return value
    text = str(value)
    if text == "":
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> str:
    from .fs import atomic_write_text
    from .hashes import sha256_bytes

    text = "".join(canonical_json(row) + "\n" for row in rows)
    atomic_write_text(path, text)
    return sha256_bytes(text.encode("utf-8"))

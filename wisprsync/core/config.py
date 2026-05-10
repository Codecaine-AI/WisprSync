from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from wisprsync.core.errors import WisprSyncError
from wisprsync.core.paths import config_path
from wisprsync.source.discovery import discover_sources
from wisprsync.source.history import history_count


def load_config(root: Path) -> dict[str, Any]:
    path = config_path(root)
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def write_config(root: Path, config: dict[str, Any]) -> None:
    path = config_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(config, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def choose_source(source_arg: str | None) -> Path:
    if source_arg:
        source = Path(source_arg).expanduser()
        if not source.exists():
            raise WisprSyncError(f"source database does not exist: {source}")
        count = history_count(source)
        if count is None:
            raise WisprSyncError(f"source database is not a readable Wispr Flow database: {source}")
        return source
    discovered = discover_sources()
    if not discovered:
        raise WisprSyncError("could not find a Wispr Flow flow.sqlite database")
    return Path(discovered[0]["path"]).expanduser()

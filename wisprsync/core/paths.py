from __future__ import annotations

from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def config_path(root: Path) -> Path:
    return root / ".wisprsync" / "config.json"


def resolve_output(root: Path, output: str | None) -> Path:
    raw = output or "data"
    path = Path(raw).expanduser()
    if not path.is_absolute():
        path = root / path
    return path


def relative_to_output(path: Path, output: Path) -> str:
    return path.relative_to(output).as_posix()

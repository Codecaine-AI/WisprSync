from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path


def atomic_replace_dir(temp_dir: Path, target_dir: Path) -> None:
    target_dir.parent.mkdir(parents=True, exist_ok=True)
    backup_dir: Path | None = None
    if target_dir.exists():
        backup_dir = target_dir.with_name(f".{target_dir.name}.replace-{os.getpid()}")
        if backup_dir.exists():
            shutil.rmtree(backup_dir)
        target_dir.rename(backup_dir)
    try:
        temp_dir.rename(target_dir)
        if backup_dir and backup_dir.exists():
            shutil.rmtree(backup_dir)
    except Exception:
        if target_dir.exists():
            shutil.rmtree(target_dir)
        if backup_dir and backup_dir.exists():
            backup_dir.rename(target_dir)
        raise


def atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.tmp-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
        Path(tmp_name).replace(path)
    except Exception:
        Path(tmp_name).unlink(missing_ok=True)
        raise

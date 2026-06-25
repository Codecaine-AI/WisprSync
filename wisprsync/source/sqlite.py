from __future__ import annotations

import sqlite3
from pathlib import Path
from urllib.parse import quote


def source_backup_dir(root: Path) -> Path:
    return root / ".wisprsync-cache" / "source-backups"


def sqlite_uri(path: Path, immutable: bool = False) -> str:
    resolved = path.expanduser().resolve()
    uri = f"file:{quote(str(resolved))}?mode=ro"
    if immutable:
        uri += "&immutable=1"
    return uri


def connect_readonly(path: Path, immutable: bool = False) -> sqlite3.Connection:
    conn = sqlite3.connect(sqlite_uri(path, immutable=immutable), uri=True, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("pragma query_only = on")
    return conn


def has_table(conn: sqlite3.Connection, table: str) -> bool:
    row = conn.execute(
        "select 1 from sqlite_master where type='table' and name=? limit 1",
        (table,),
    ).fetchone()
    return row is not None


def create_snapshot(source: Path, root: Path, run_id: str) -> tuple[Path, str, str | None]:
    snapshot_dir = source_backup_dir(root)
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    snapshot = snapshot_dir / f"{run_id}.sqlite"
    try:
        src = sqlite3.connect(sqlite_uri(source), uri=True, timeout=30)
        dst = sqlite3.connect(snapshot)
        with dst:
            src.backup(dst)
        src.close()
        dst.close()
        return snapshot, "sqlite_backup", None
    except sqlite3.Error as exc:
        try:
            if "src" in locals():
                src.close()
            if "dst" in locals():
                dst.close()
        finally:
            if snapshot.exists():
                snapshot.unlink()
        return source, "immutable_source_fallback", str(exc)


def prune_source_backups(root: Path, keep: int = 1) -> list[Path]:
    if keep < 1:
        raise ValueError("keep must be at least 1")
    snapshot_dir = source_backup_dir(root)
    if not snapshot_dir.exists():
        return []

    snapshots = sorted(
        (path for path in snapshot_dir.glob("*.sqlite") if path.is_file() or path.is_symlink()),
        key=_snapshot_sort_key,
        reverse=True,
    )
    retained = {path.name for path in snapshots[:keep]}
    removed: list[Path] = []

    for snapshot in snapshots[keep:]:
        for path in _snapshot_files(snapshot):
            if _unlink_file(path):
                removed.append(path)

    for sidecar in list(snapshot_dir.glob("*.sqlite-wal")) + list(snapshot_dir.glob("*.sqlite-shm")):
        base_name = sidecar.name.removesuffix("-wal").removesuffix("-shm")
        if base_name not in retained and _unlink_file(sidecar):
            removed.append(sidecar)

    return removed


def _snapshot_sort_key(path: Path) -> tuple[int, str]:
    try:
        return path.stat().st_mtime_ns, path.name
    except OSError:
        return 0, path.name


def _snapshot_files(snapshot: Path) -> tuple[Path, Path, Path]:
    return (
        snapshot,
        snapshot.with_name(f"{snapshot.name}-wal"),
        snapshot.with_name(f"{snapshot.name}-shm"),
    )


def _unlink_file(path: Path) -> bool:
    if not path.exists() and not path.is_symlink():
        return False
    if not path.is_file() and not path.is_symlink():
        return False
    path.unlink()
    return True

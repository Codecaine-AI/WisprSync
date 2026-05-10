from __future__ import annotations

import sqlite3
from pathlib import Path
from urllib.parse import quote


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
    snapshot_dir = root / ".wisprsync-cache" / "source-backups"
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

from __future__ import annotations

import json
import shutil
import sqlite3
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from wisprsync.core.paths import relative_to_output
from wisprsync.support.fs import atomic_replace_dir
from wisprsync.support.json import write_json
from wisprsync.support.time import compact_ts, parse_timestamp


def record_parts(timestamp_utc: datetime | None, record_id: str) -> tuple[list[str], str]:
    if timestamp_utc is None:
        return ["unknown", "unknown", "unknown"], f"unknown-time_{record_id}"
    dt = timestamp_utc.astimezone(timezone.utc)
    return [dt.strftime("%Y"), dt.strftime("%m"), dt.strftime("%d")], f"{compact_ts(dt)}_{record_id}"


def build_existing_index(output: Path) -> tuple[dict[str, Path], list[str]]:
    index: dict[str, Path] = {}
    errors: list[str] = []
    records_dir = output / "records"
    if not records_dir.exists():
        return index, errors
    for metadata_path in records_dir.glob("*/*/*/*/metadata.json"):
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"invalid metadata file {metadata_path}: {exc}")
            continue
        record_id = metadata.get("id")
        if not record_id:
            errors.append(f"metadata missing id: {metadata_path}")
            continue
        if record_id in index:
            errors.append(f"duplicate exported record id {record_id}: {index[record_id]} and {metadata_path.parent}")
            continue
        index[record_id] = metadata_path.parent
    return index, errors


def preflight_source(conn: sqlite3.Connection, output: Path, limit: int | None) -> tuple[dict[str, Path], list[str]]:
    errors: list[str] = []
    duplicate = conn.execute(
        'select transcriptEntityId, count(*) from "History" group by transcriptEntityId having count(*) > 1 limit 10'
    ).fetchall()
    if duplicate:
        errors.extend(f"duplicate source transcriptEntityId: {row[0]}" for row in duplicate)

    existing_index, existing_errors = build_existing_index(output)
    errors.extend(existing_errors)

    seen_paths: dict[str, str] = {}
    sql = 'select transcriptEntityId, timestamp from "History" order by timestamp, transcriptEntityId'
    if limit is not None:
        sql += f" limit {int(limit)}"
    for row in conn.execute(sql):
        record_id = row["transcriptEntityId"]
        if not record_id:
            continue
        parts, name = record_parts(parse_timestamp(row["timestamp"]), record_id)
        rel_path = "/".join(["records", *parts, name])
        if rel_path in seen_paths and seen_paths[rel_path] != record_id:
            errors.append(f"record path collision: {rel_path}")
        seen_paths[rel_path] = record_id
        target = output / rel_path
        metadata_path = target / "metadata.json"
        if metadata_path.exists():
            try:
                metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                errors.append(f"invalid existing metadata at {metadata_path}: {exc}")
                continue
            if metadata.get("id") != record_id:
                errors.append(f"existing record path has different id: {metadata_path}")
    return existing_index, errors


def write_record(
    record_dir: Path,
    metadata: dict[str, Any],
    row: dict[str, Any],
    blobs: dict[str, bytes | None],
) -> None:
    temp_parent = record_dir.parent
    temp_parent.mkdir(parents=True, exist_ok=True)
    temp_dir = Path(tempfile.mkdtemp(prefix=f".{record_dir.name}.tmp-", dir=temp_parent))
    try:
        write_json(temp_dir / "metadata.json", metadata)
        if metadata["files"]["raw_transcript"]:
            (temp_dir / metadata["files"]["raw_transcript"]).write_text(row["asrText"], encoding="utf-8")
        if metadata["files"]["formatted_transcript"]:
            (temp_dir / metadata["files"]["formatted_transcript"]).write_text(row["formattedText"], encoding="utf-8")
        if metadata["files"]["audio"]:
            (temp_dir / metadata["files"]["audio"]).write_bytes(blobs["audio"])
        if metadata["files"]["screenshot"]:
            (temp_dir / metadata["files"]["screenshot"]).write_bytes(blobs["screenshot"])
        atomic_replace_dir(temp_dir, record_dir)
    finally:
        if temp_dir.exists():
            shutil.rmtree(temp_dir)


def existing_source_hash(record_dir: Path) -> str | None:
    metadata_path = record_dir / "metadata.json"
    if not metadata_path.exists():
        return None
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return metadata.get("integrity", {}).get("source_row_sha256")

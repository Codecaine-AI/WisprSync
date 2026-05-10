from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from wisprsync.core.constants import SCHEMA_VERSION
from wisprsync.core.paths import relative_to_output
from wisprsync.export.metadata import bool_or_none
from wisprsync.support.json import canonical_json, write_json
from wisprsync.support.time import iso_z, parse_timestamp, utc_now


def history_index_object(
    row: dict[str, Any],
    metadata: dict[str, Any],
    paths: dict[str, Any],
    record_dir: Path,
    output: Path,
) -> dict[str, Any]:
    timestamp_utc = parse_timestamp(row.get("timestamp"))
    return {
        "schema_version": SCHEMA_VERSION,
        "id": row.get("transcriptEntityId"),
        "timestamp_utc": iso_z(timestamp_utc) if timestamp_utc else None,
        "date_utc": timestamp_utc.date().isoformat() if timestamp_utc else None,
        "status": row.get("status"),
        "app": row.get("app"),
        "url": row.get("url"),
        "num_words": row.get("numWords"),
        "duration_seconds": row.get("duration"),
        "speech_duration_seconds": row.get("speechDuration"),
        "asr_text": row.get("asrText"),
        "formatted_text": row.get("formattedText"),
        "edited_text": row.get("editedText"),
        "pasted_text": row.get("pastedText"),
        "default_asr_text": row.get("defaultAsrText"),
        "fallback_asr_text": row.get("fallbackAsrText"),
        "default_formatted_text": row.get("defaultFormattedText"),
        "fallback_formatted_text": row.get("fallbackFormattedText"),
        "raw_transcript_path": paths["raw_transcript_path"],
        "formatted_transcript_path": paths["formatted_transcript_path"],
        "audio_path": paths["audio_path"],
        "audio_sha256": metadata["media"]["audio"]["sha256"],
        "screenshot_path": paths["screenshot_path"],
        "screenshot_sha256": metadata["media"]["screenshot"]["sha256"],
        "metadata_path": paths["metadata_path"],
        "record_path": relative_to_output(record_dir, output),
        "source_row_sha256": metadata["integrity"]["source_row_sha256"],
    }


def dictionary_row_to_object(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "id": row["id"],
        "phrase": row["phrase"],
        "replacement": row["replacement"],
        "team_dictionary_id": row["teamDictionaryId"],
        "last_used": row["lastUsed"],
        "frequency_used": row["frequencyUsed"],
        "remote_frequency_used": row["remoteFrequencyUsed"],
        "manual_entry": bool_or_none(row["manualEntry"]),
        "source": row["source"],
        "observed_source": row["observedSource"],
        "is_snippet": bool_or_none(row["isSnippet"]),
        "is_starred": bool_or_none(row["isStarred"]),
        "is_deleted": bool_or_none(row["isDeleted"]),
        "created_at": row["createdAt"],
        "modified_at": row["modifiedAt"],
    }


def write_run_report(output: Path, run_report: dict[str, Any]) -> None:
    started = parse_timestamp(run_report["started_at_utc"]) or utc_now()
    run_path = output / "runs" / f"{started:%Y}" / f"{started:%m}" / f"{started:%d}" / f"{run_report['run_id']}.json"
    write_json(run_path, run_report)
    summary = {
        "schema_version": run_report["schema_version"],
        "run_id": run_report["run_id"],
        "started_at_utc": run_report["started_at_utc"],
        "finished_at_utc": run_report["finished_at_utc"],
        "status": run_report["status"],
        **run_report["results"],
        "run_report_path": relative_to_output(run_path, output),
    }
    runs_path = output / "indexes" / "runs.jsonl"
    runs_path.parent.mkdir(parents=True, exist_ok=True)
    with runs_path.open("a", encoding="utf-8") as handle:
        handle.write(canonical_json(summary) + "\n")


def print_run_summary(run_report: dict[str, Any], output: Path) -> None:
    results = run_report["results"]
    print(f"Run {run_report['run_id']}: {run_report['status']}")
    print(f"Output: {output}")
    print(
        "Rows: {source_rows_seen}; created: {records_created}; updated: {records_updated}; "
        "unchanged: {records_unchanged}; missing-from-source: {records_missing_from_source}; errors: {errors}".format(
            **results
        )
    )
    if run_report["errors"]:
        print("Errors:")
        for error in run_report["errors"]:
            print(f"- {error}")

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from wisprsync.core.config import choose_source, load_config
from wisprsync.core.constants import DICTIONARY_COLUMNS, SCHEMA_VERSION
from wisprsync.core.errors import WisprSyncError
from wisprsync.core.paths import relative_to_output, repo_root, resolve_output
from wisprsync.core.safety import ensure_child, validate_export_paths
from wisprsync.export.indexes import (
    dictionary_row_to_object,
    history_index_object,
    print_run_summary,
    retained_history_index_object,
    write_run_report,
)
from wisprsync.export.metadata import build_metadata
from wisprsync.export.records import existing_source_hash, preflight_source, record_parts, write_record
from wisprsync.source.history import history_select_sql, row_to_plain_dict
from wisprsync.source.sqlite import connect_readonly, create_snapshot, has_table
from wisprsync.support.json import write_json, write_jsonl
from wisprsync.support.time import compact_ts, iso_z, parse_timestamp, utc_now


def command_export(args: Any) -> int:
    root = repo_root()
    config = load_config(root)
    source_value = args.source or config.get("source_database")
    source = choose_source(source_value)
    output_value = args.output or config.get("output_directory")
    if not output_value:
        raise WisprSyncError("export requires --output or a configured output_directory; run setup first")
    output = resolve_output(root, output_value)
    validate_export_paths(root, source, output, getattr(args, "allow_unsafe_output", False))
    include_screenshots = config.get("include_screenshots", True)
    if args.include_screenshots:
        include_screenshots = True
    if args.no_screenshots:
        include_screenshots = False

    started_at = utc_now()
    run_id = compact_ts(started_at)
    snapshot, snapshot_mode, snapshot_error = create_snapshot(source, root, run_id)
    immutable = snapshot_mode == "immutable_source_fallback"

    output.mkdir(parents=True, exist_ok=True)
    indexes_dir = output / "indexes"
    indexes_dir.mkdir(parents=True, exist_ok=True)

    run_report: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "started_at_utc": iso_z(started_at),
        "finished_at_utc": None,
        "status": "running",
        "source_snapshot": {
            "database_path": str(source.expanduser().resolve()),
            "snapshot_path": str(snapshot),
            "snapshot_mode": snapshot_mode,
            "snapshot_error": snapshot_error,
        },
        "results": {
            "source_rows_seen": 0,
            "records_created": 0,
            "records_updated": 0,
            "records_unchanged": 0,
            "records_skipped": 0,
            "records_missing_from_source": 0,
            "collisions": 0,
            "errors": 0,
        },
        "changes": [],
        "errors": [],
    }

    try:
        with connect_readonly(snapshot, immutable=immutable) as conn:
            if not has_table(conn, "History"):
                raise WisprSyncError("source database does not contain History table")
            existing_index, preflight_errors = preflight_source(conn, output, args.limit)
            if preflight_errors:
                run_report["results"]["collisions"] = len(preflight_errors)
                run_report["errors"].extend(preflight_errors)
                raise WisprSyncError("preflight failed")

            previous_missing_since = read_previous_missing_since(indexes_dir / "history.jsonl")
            history_rows: list[dict[str, Any]] = []
            source_ids: set[str] = set()
            min_timestamp = None
            max_timestamp = None
            records_with_audio = 0
            records_with_screenshot = 0

            for sqlite_row in conn.execute(history_select_sql(args.limit)):
                row = row_to_plain_dict(sqlite_row)
                run_report["results"]["source_rows_seen"] += 1
                record_id = row["transcriptEntityId"]
                if not record_id:
                    run_report["results"]["records_skipped"] += 1
                    continue
                source_ids.add(record_id)
                timestamp_utc = parse_timestamp(row.get("timestamp"))
                if timestamp_utc:
                    min_timestamp = timestamp_utc if min_timestamp is None else min(min_timestamp, timestamp_utc)
                    max_timestamp = timestamp_utc if max_timestamp is None else max(max_timestamp, timestamp_utc)
                parts, record_name = record_parts(timestamp_utc, record_id)
                record_dir = output / "records" / parts[0] / parts[1] / parts[2] / record_name
                metadata, paths, blobs = build_metadata(row, source, output, record_dir, started_at, include_screenshots)
                old_dir = existing_index.get(record_id)
                old_hash = existing_source_hash(old_dir) if old_dir else None
                current_hash = metadata["integrity"]["source_row_sha256"]

                if metadata["media"]["audio"]["present"]:
                    records_with_audio += 1
                if metadata["media"]["screenshot"]["present"]:
                    records_with_screenshot += 1

                if args.dry_run:
                    action = "unchanged" if old_hash == current_hash else ("updated" if old_dir else "created")
                elif old_hash == current_hash and old_dir == record_dir:
                    action = "unchanged"
                else:
                    action = "updated" if old_dir else "created"
                    ensure_child(output / "records", record_dir, "record directory")
                    write_record(record_dir, metadata, row, blobs)
                    if old_dir and old_dir != record_dir and old_dir.exists():
                        ensure_child(output / "records", old_dir, "old record directory")
                        shutil.rmtree(old_dir)

                if action == "created":
                    run_report["results"]["records_created"] += 1
                elif action == "updated":
                    run_report["results"]["records_updated"] += 1
                else:
                    run_report["results"]["records_unchanged"] += 1

                if action != "unchanged":
                    run_report["changes"].append(
                        {
                            "id": record_id,
                            "action": action,
                            "record_path": relative_to_output(record_dir, output),
                        }
                    )

                history_rows.append(history_index_object(row, metadata, paths, record_dir, output))

            missing = sorted(set(existing_index) - source_ids)
            run_report["results"]["records_missing_from_source"] = len(missing)
            retained_missing_count = 0
            for record_id in missing:
                record_dir = existing_index[record_id]
                try:
                    metadata = json.loads((record_dir / "metadata.json").read_text(encoding="utf-8"))
                except Exception as exc:
                    run_report["errors"].append(f"could not retain missing record {record_id}: {exc}")
                    run_report["results"]["errors"] += 1
                    continue
                missing_since = previous_missing_since.get(record_id) or run_id
                history_rows.append(retained_history_index_object(metadata, record_dir, output, missing_since))
                retained_missing_count += 1

            dictionary_rows: list[dict[str, Any]] = []
            if has_table(conn, "Dictionary"):
                columns = ", ".join(f'"{column}"' for column in DICTIONARY_COLUMNS)
                for row in conn.execute(f'select {columns} from "Dictionary" order by phrase, id'):
                    dictionary_rows.append(dictionary_row_to_object(row))

            if not args.dry_run:
                history_hash = write_jsonl(indexes_dir / "history.jsonl", history_rows)
                dictionary_hash = write_jsonl(indexes_dir / "dictionary.jsonl", dictionary_rows)
                manifest = {
                    "schema_version": SCHEMA_VERSION,
                    "dataset": {
                        "name": "wispr-flow-export",
                        "created_at_utc": iso_z(started_at),
                        "updated_at_utc": iso_z(started_at),
                    },
                    "source": {
                        "application": "Wispr Flow",
                        "database_path": str(source.expanduser().resolve()),
                        "source_table": "History",
                    },
                    "counts": {
                        "history_rows": len(history_rows),
                        "source_history_rows": len(source_ids),
                        "active_records": len(source_ids),
                        "retained_missing_from_source_records": retained_missing_count,
                        "total_records": len(history_rows),
                        "records": len(history_rows),
                        "records_with_audio": records_with_audio,
                        "records_with_screenshot": records_with_screenshot,
                        "dictionary_rows": len(dictionary_rows),
                    },
                    "date_range": {
                        "min_timestamp_utc": iso_z(min_timestamp) if min_timestamp else None,
                        "max_timestamp_utc": iso_z(max_timestamp) if max_timestamp else None,
                    },
                    "indexes": {
                        "history_jsonl": "indexes/history.jsonl",
                        "dictionary_jsonl": "indexes/dictionary.jsonl",
                        "runs_jsonl": "indexes/runs.jsonl",
                    },
                    "latest_run": {
                        "run_id": run_id,
                        "path": f"runs/{started_at:%Y/%m/%d}/{run_id}.json",
                        "status": "success",
                    },
                    "integrity": {
                        "history_jsonl_sha256": history_hash,
                        "dictionary_jsonl_sha256": dictionary_hash,
                        "record_count": len(history_rows),
                    },
                }
                write_json(output / "manifest.json", manifest)

            run_report["status"] = "dry_run" if args.dry_run else "success"
    except Exception as exc:
        run_report["status"] = "failed"
        run_report["results"]["errors"] += 1
        if not run_report["errors"]:
            run_report["errors"].append(str(exc))
        if not isinstance(exc, WisprSyncError):
            raise
    finally:
        run_report["finished_at_utc"] = iso_z(utc_now())
        if not args.dry_run:
            write_run_report(output, run_report)

    print_run_summary(run_report, output)
    return 0 if run_report["status"] in {"success", "dry_run"} else 1


def read_previous_missing_since(history_path: Path) -> dict[str, str]:
    if not history_path.exists():
        return {}
    result: dict[str, str] = {}
    for line in history_path.read_text(encoding="utf-8").splitlines():
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if row.get("source_status") != "missing_from_source":
            continue
        record_id = row.get("id")
        missing_since = row.get("missing_from_source_since_run_id")
        if record_id and missing_since:
            result[record_id] = missing_since
    return result

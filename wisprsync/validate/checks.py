from __future__ import annotations

import json
from pathlib import Path

from wisprsync.support.hashes import sha256_bytes


def read_manifest(path: Path, errors: list[str]) -> dict | None:
    if not path.exists():
        errors.append(f"missing manifest: {path}")
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append(f"invalid manifest JSON: {exc}")
        return None


def validate_history_index(history_path: Path, errors: list[str]) -> set[str]:
    history_ids: set[str] = set()
    if not history_path.exists():
        errors.append(f"missing history index: {history_path}")
        return history_ids

    for lineno, line in enumerate(history_path.read_text(encoding="utf-8").splitlines(), start=1):
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"invalid history.jsonl line {lineno}: {exc}")
            continue
        record_id = obj.get("id")
        if record_id in history_ids:
            errors.append(f"duplicate id in history.jsonl: {record_id}")
        history_ids.add(record_id)
    return history_ids


def validate_record_files(exported: dict[str, Path], errors: list[str]) -> None:
    for record_id, record_dir in exported.items():
        metadata_path = record_dir / "metadata.json"
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        if metadata.get("id") != record_id:
            errors.append(f"metadata id mismatch: {metadata_path}")
        for key in ("raw_transcript", "formatted_transcript"):
            rel = metadata.get("files", {}).get(key)
            if rel and not (record_dir / rel).exists():
                errors.append(f"missing transcript file for {record_id}: {rel}")
        for media_key in ("audio", "screenshot"):
            info = metadata.get("media", {}).get(media_key, {})
            rel = metadata.get("files", {}).get(media_key)
            if info.get("present"):
                if not rel:
                    errors.append(f"metadata missing {media_key} path for {record_id}")
                    continue
                path = record_dir / rel
                if not path.exists():
                    errors.append(f"missing {media_key} file for {record_id}: {path}")
                    continue
                expected_hash = info.get("sha256")
                if expected_hash and sha256_bytes(path.read_bytes()) != expected_hash:
                    errors.append(f"{media_key} hash mismatch for {record_id}: {path}")


def validate_jsonl(path: Path, errors: list[str], warnings: list[str], optional: bool = False) -> None:
    if not path.exists():
        if optional:
            warnings.append(f"missing {path.name}; no export run may have written it yet")
        else:
            errors.append(f"missing {path.name}")
        return
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        try:
            json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"invalid {path.name} line {lineno}: {exc}")


def print_validation(errors: list[str], warnings: list[str]) -> None:
    if errors:
        print(f"Validation failed: {len(errors)} error(s)")
        for error in errors:
            print(f"- {error}")
    else:
        print("Validation passed")
    if warnings:
        print(f"Warnings: {len(warnings)}")
        for warning in warnings:
            print(f"- {warning}")

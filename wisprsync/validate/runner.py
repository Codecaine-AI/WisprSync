from __future__ import annotations

from typing import Any

from wisprsync.core.config import load_config
from wisprsync.core.paths import repo_root, resolve_output
from wisprsync.export.records import build_existing_index
from wisprsync.validate.checks import (
    print_validation,
    read_manifest,
    validate_history_index,
    validate_jsonl,
    validate_record_files,
)


def command_validate(args: Any) -> int:
    root = repo_root()
    config = load_config(root)
    output = resolve_output(root, args.output or config.get("output_directory") or "data")
    errors: list[str] = []
    warnings: list[str] = []

    manifest = read_manifest(output / "manifest.json", errors)
    if manifest is None:
        print_validation(errors, warnings)
        return 1

    exported, existing_errors = build_existing_index(output)
    errors.extend(existing_errors)

    history_ids = validate_history_index(output / "indexes" / "history.jsonl", errors)
    validate_record_files(exported, errors)

    expected_records = manifest.get("counts", {}).get("records")
    if expected_records is not None and expected_records != len(history_ids):
        errors.append(f"manifest record count {expected_records} != history index count {len(history_ids)}")
    if history_ids and set(exported) - history_ids:
        warnings.append(f"{len(set(exported) - history_ids)} exported records are missing from history index")

    validate_jsonl(output / "indexes" / "dictionary.jsonl", errors, warnings)
    validate_jsonl(output / "indexes" / "runs.jsonl", errors, warnings, optional=True)

    print_validation(errors, warnings)
    return 1 if errors else 0

---
covers: How current WisprSync code maps History rows into metadata, record files, indexes, manifests, and run reports.
concepts: [metadata, indexes, hashing, records]
design_refs: [10-system-design/10-data-structure/10-wispr-flow-source-shape.md, 10-system-design/10-data-structure/20-wisprsync-output-shape.md, 10-system-design/20-exporting/10-folder-export.md]
depends-on: [20-implementation/10-export-pipeline/00-overview.md]
---

# Source To Record Mapping

The source-to-record mapping lives in the exporter and record helper modules. It reads a fixed set of `History` columns, converts each row into canonical metadata and optional files, and emits compact index rows for analysis.

---

## Source Selection

`wisprsync/source/sqlite.py` defines read-only SQLite access and snapshot creation. `wisprsync/source/discovery.py` checks the known macOS database candidates and ranks valid Wispr Flow databases by `History` row count. `history_select_sql()` in `wisprsync/source/history.py` selects the configured `HISTORY_COLUMNS` in timestamp and ID order.

The exported `History` columns are listed in `wisprsync/core/constants.py`. They include identity, transcript text variants, status, app context, media blobs, quality fields, edit fields, language, platform, and timing fields.

## Record Naming

`record_parts()` in `wisprsync/export/records.py` converts a parsed UTC timestamp and record ID into:

```text
records/YYYY/MM/DD/{timestamp_compact_utc}_{transcriptEntityId}/
```

If timestamp parsing fails, the path uses:

```text
records/unknown/unknown/unknown/unknown-time_{transcriptEntityId}/
```

The preflight step builds an existing record index from `metadata.json` files, checks duplicate source IDs, checks path collisions, and verifies that existing record directories contain the expected ID.

## Metadata Construction

`build_metadata()` in `wisprsync/export/metadata.py` is the central implementation of the canonical record object. It maps source fields into these metadata sections:

| Metadata section | Source fields and computed values |
| --- | --- |
| `source` | source app label, table name, primary key, database path |
| `timestamps` | parsed UTC timestamp, local timestamp, timezone offset, export time |
| `status` | Wispr status, edited text status, upload/share/archive flags |
| `text` | ASR, formatted, edited, pasted, default, and fallback text variants |
| `text_stats` | word count, duration, speech duration |
| `media` | audio/screenshot presence, format, size, SHA-256 |
| `context` | target app, URL, additional context JSON, textbox contents, conversation, mic, language, platform, app version |
| `quality` | latency, log probability, divergence scores, fallback/external-ASR flags |
| `edits` | user edit metadata, corrected word count, dictionary replacement count, reverted-AI flag |
| `files` | relative names for files present in the record directory |
| `integrity` | source row hash, record content hash, exporter version |

Text fields are written as separate files only for `asrText` and `formattedText`. Other transcript variants remain in JSON metadata and JSONL indexes.

## File Writing

`write_record()` in `wisprsync/export/records.py` creates a temporary sibling directory, writes the record contents into it, and atomically replaces the target record directory.

The record writer creates:

- `metadata.json` for every record,
- `raw_transcript.txt` when `asrText` is non-empty,
- `formatted_transcript.txt` when `formattedText` is non-empty,
- `audio.wav` when `audio` is present,
- `screenshot.png` when screenshots are enabled and `screenshot` is present.

## Index Generation

`history_index_object()` in `wisprsync/export/indexes.py` produces one compact JSON object per exported `History` row. The object includes the key analysis fields, relative paths to generated files, media hashes, the record directory path, and `source_row_sha256`.

Dictionary rows are exported separately through `dictionary_row_to_object()` in `wisprsync/export/indexes.py` and written to `indexes/dictionary.jsonl`. Dictionary export uses configured `DICTIONARY_COLUMNS` and sorts by phrase and ID.

## Manifest And Run Reports

`command_export()` in `wisprsync/export/runner.py` writes `manifest.json` with dataset timestamps, source database path, counts, date range, index paths, latest run, and index hashes.

`write_run_report()` in `wisprsync/export/indexes.py` stores the full run report under:

```text
runs/YYYY/MM/DD/{run_id}.json
```

and appends a compact summary to:

```text
indexes/runs.jsonl
```

## Related Files

- `bin/sync` - repo-local entry point for sync.
- `wisprsync/cli/main.py` - CLI parser and command dispatch.
- `wisprsync/cli/commands.py` - setup, sync, and doctor command functions.
- `wisprsync/export/runner.py` - export loop, manifest construction, and run status handling.
- `wisprsync/export/metadata.py` - metadata object construction and source/content hashes.
- `wisprsync/export/records.py` - record naming, existing-record indexing, preflight checks, and atomic record writes.
- `wisprsync/export/indexes.py` - history index objects, dictionary index objects, run report writing, and run summaries.
- `wisprsync/source/sqlite.py` - read-only SQLite connection and snapshot handling.
- `wisprsync/source/discovery.py` - source database discovery.
- `wisprsync/source/history.py` - History row selection and row conversion.
- `wisprsync/validate/runner.py` - validation command orchestration.
- `wisprsync/validate/checks.py` - validation of manifest, indexes, records, hashes, and missing files.

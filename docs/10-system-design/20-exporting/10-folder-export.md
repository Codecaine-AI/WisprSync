---
covers: The default WisprSync export mode that writes canonical data to a user-specified folder.
concepts: [folder-export, output-directory, sync, hashes]
depends-on: [10-system-design/10-data-structure/20-wisprsync-output-shape.md]
---

# Folder Export

Folder export is the base WisprSync behavior. It reads Wispr Flow data and writes the canonical export tree to the output directory the user specifies, usually `data/` or a folder inside a cloud-synced directory.

---

## Recommended Use

For most users, the easiest cloud sync path is to choose an output folder that is already synced by another tool:

```text
~/Dropbox/WisprSync
~/Library/Mobile Documents/com~apple~CloudDocs/WisprSync
~/Google Drive/My Drive/WisprSync
~/OneDrive/WisprSync
```

WisprSync does not need to understand those cloud providers. It just writes files to the folder, and the user's existing sync tool uploads them.

## Basic Flow

For each run:

1. Resolve the source Wispr Flow SQLite database.
2. Resolve the output directory.
3. Read rows from `History`.
4. For each row, build the record path from timestamp and `transcriptEntityId`.
5. Write the record directory:
   - `metadata.json`
   - `raw_transcript.txt` when `asrText` exists
   - `formatted_transcript.txt` when `formattedText` exists
   - `audio.wav` when audio exists
   - `screenshot.png` when screenshots are enabled and a screenshot exists
6. Write `indexes/history.jsonl`.
7. Regenerate `indexes/dictionary.jsonl`.
8. Write `manifest.json`.
9. Write a run report under `runs/` and append a summary to `indexes/runs.jsonl`.

## Record Identity

The record ID is:

```text
History.transcriptEntityId
```

The timestamp only organizes the folder path:

```text
records/YYYY/MM/DD/{timestamp_compact_utc}_{transcriptEntityId}/
```

If the same `transcriptEntityId` appears on a later run, WisprSync treats it as the same record.

## Repeat Runs

On repeat export:

- missing exported record: create it,
- same ID and same source hash: leave it alone,
- same ID and changed source hash: replace the record files,
- same ID but timestamp path changed: move the record after confirming the existing `metadata.json` has the same ID,
- exported ID missing from the source database: report it in the run report, but do not delete it by default.

## Hashes

Hashes are only there to make repeat exports practical and check the files that were written.

| Hash | Meaning |
| --- | --- |
| `source_row_sha256` | Fingerprint of the exported source row content. Used to decide whether a record changed. |
| `record_content_sha256` | Fingerprint of the exported metadata plus generated file hashes. Used to validate the written record. |
| `audio_sha256` | Fingerprint of exported audio bytes. |
| `screenshot_sha256` | Fingerprint of exported screenshot bytes. |

`exported_at_utc` is excluded from `source_row_sha256` so an unchanged Wispr Flow row has the same hash across runs.

## Safety Checks

The exporter should stop instead of guessing if it sees an unsafe state:

- duplicate `transcriptEntityId` values in the source,
- two source rows resolving to the same record path,
- an existing record path whose `metadata.json` contains a different ID,
- duplicate IDs in `indexes/history.jsonl`.

These are hard failures because choosing a winner could corrupt the exported data.

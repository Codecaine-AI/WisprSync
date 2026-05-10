---
covers: The canonical WisprSync output shape for records, metadata, indexes, manifests, and run reports.
concepts: [wisprsync, output, metadata, indexes, file-tree]
depends-on: [10-system-design/10-data-structure/10-wispr-flow-source-shape.md]
---

# WisprSync Output Shape

WisprSync turns Wispr Flow's local SQLite rows into a canonical `data/` folder that is easy to own, search, validate, and load into analysis tools. The output structure is designed around one durable identity, `History.transcriptEntityId`, with large blobs stored as normal files and query-friendly JSONL indexes generated alongside per-record folders.

---

## Parsed Record Shape

WisprSync parses each `History` row into one canonical record. The record has a structured `metadata.json`, optional text files, optional media files, and a compact row in `indexes/history.jsonl`.

```text
record
├── metadata.json              canonical structured object
├── raw_transcript.txt         optional text from History.asrText
├── formatted_transcript.txt   optional text from History.formattedText
├── audio.wav                  optional bytes from History.audio
└── screenshot.png             optional bytes from History.screenshot
```

Transcript option files are convenience artifacts for direct search and reading. They contain only the source text value. They do not include labels, separators, or metadata.

Fields that are not first-class files stay in `metadata.json` and `indexes/history.jsonl`. This includes `editedText`, `pastedText`, fallback/default transcript variants, app context, URLs, timings, language, quality metadata, and edit metadata.

## Metadata Object

The canonical metadata shape is:

```json
{
  "schema_version": 1,
  "id": "transcriptEntityId",
  "source": {
    "app": "Wispr Flow",
    "source_table": "History",
    "source_primary_key": "transcriptEntityId",
    "source_database_path": "~/Library/Application Support/Wispr Flow/flow.sqlite"
  },
  "timestamps": {
    "timestamp_utc": "2026-05-02T19:22:06.993Z",
    "timestamp_local": "2026-05-02T14:22:06.993-05:00",
    "timezone_offset_minutes": -300,
    "exported_at_utc": "2026-05-09T17:30:00.000Z"
  },
  "status": {
    "wispr_status": "formatted",
    "edited_text_status": "NOT_EXTRACTED",
    "needs_uploading": false,
    "share_type": "no",
    "is_archived": false
  },
  "text": {
    "asr": "Raw ASR transcript text.",
    "formatted": "Formatted transcript text.",
    "edited": null,
    "pasted": "Text pasted into the target app.",
    "default_asr": null,
    "fallback_asr": null,
    "default_formatted": null,
    "fallback_formatted": null
  },
  "text_stats": {
    "num_words": 42,
    "duration_seconds": 12.34,
    "speech_duration_seconds": 12.2
  },
  "media": {
    "audio": {
      "path": "audio.wav",
      "present": true,
      "format": "wav_pcm_s16le_16000hz_mono",
      "size_bytes": 529708,
      "sha256": "..."
    },
    "screenshot": {
      "path": "screenshot.png",
      "present": true,
      "format": "png",
      "size_bytes": 123456,
      "sha256": "..."
    }
  },
  "context": {
    "target_app": "com.google.Chrome",
    "target_url": "https://example.com/path",
    "conversation_id": "conversation-id-if-present",
    "mic_device": "microphone-if-present",
    "language": "en",
    "detected_language": "en",
    "platform": "desktop",
    "transcript_origin": "internal",
    "app_version": "1.5.113",
    "textbox_contents": null,
    "additional_context": {}
  },
  "quality": {
    "average_log_prob": -0.1,
    "formatting_divergence_score": null,
    "fallback_asr_divergence_score": null,
    "fallback_formatting_divergence_score": null,
    "used_fallback_asr": false,
    "used_fallback_formatting": false,
    "called_external_asr": false,
    "client_network_latency": null,
    "e2e_latency": null
  },
  "edits": {
    "user_edit_metadata": {},
    "num_words_corrected": null,
    "num_dictionary_replacements": null,
    "has_reverted_ai": false
  },
  "files": {
    "metadata": "metadata.json",
    "raw_transcript": "raw_transcript.txt",
    "formatted_transcript": "formatted_transcript.txt",
    "audio": "audio.wav",
    "screenshot": "screenshot.png"
  },
  "integrity": {
    "source_row_sha256": "...",
    "record_content_sha256": "...",
    "exporter_version": "0.1.0"
  }
}
```

## File Tree Layout

The default export root is `data/`.

```text
data/
├── manifest.json
├── indexes/
│   ├── history.jsonl
│   ├── dictionary.jsonl
│   └── runs.jsonl
├── records/
│   └── YYYY/
│       └── MM/
│           └── DD/
│               └── {timestamp_compact_utc}_{transcriptEntityId}/
│                   ├── metadata.json
│                   ├── raw_transcript.txt
│                   ├── formatted_transcript.txt
│                   ├── audio.wav
│                   └── screenshot.png
└── runs/
    └── YYYY/
        └── MM/
            └── DD/
                └── {run_id}.json
```

Example record path:

```text
records/2026/05/02/20260502T192206.993Z_73fda602-7e80-4345-90c3-9a5af36beb0e/
```

The date folders come from `History.timestamp` normalized to UTC. The record ID comes from `History.transcriptEntityId` and defines identity. If a timestamp is missing or invalid, the record is placed under:

```text
records/unknown/unknown/unknown/unknown-time_{transcriptEntityId}/
```

## Indexes

`indexes/history.jsonl` has one compact JSON object per searchable transcript record. It includes current `History` rows and previously exported records that are now missing from the source database. Current rows use `source_status: "current"`; retained rows use `source_status: "missing_from_source"` and keep the last exported text, metadata path, media paths, and hashes.

`indexes/dictionary.jsonl` is a full export of the current `Dictionary` table. It represents the latest dictionary state for the run rather than an append-only dictionary history.

`indexes/runs.jsonl` appends one compact summary object for each export run.

## Manifest And Run Reports

`manifest.json` describes the whole data zone and latest export state: dataset timestamps, source database, counts, date range, index paths, latest run, and top-level integrity hashes.

Each run writes a full report under:

```text
runs/YYYY/MM/DD/{run_id}.json
```

The run report records the source snapshot, counts for created/updated/unchanged/skipped/missing records, collision and error counts, and per-record changes.

## Placement Rules

- `metadata.json` is required for every exported record.
- Transcript option files are created only when the corresponding source field is non-empty.
- Media files are created only when the source row has the blob and the export configuration includes that media type.
- Blob bytes are never embedded in JSON.
- Paths inside indexes are relative to the output root.
- Source rows that disappear are reported as missing from source, not deleted from the export by default.
- Raw Wispr Flow app folders, cookies, session files, caches, telemetry queues, and Electron state are outside the canonical export.

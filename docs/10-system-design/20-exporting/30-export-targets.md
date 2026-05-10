---
covers: The extension model for adding export targets beyond the default folder export.
concepts: [export-targets, extensibility, remote-sync]
depends-on: [10-system-design/20-exporting/10-folder-export.md]
---

# Export Targets

Export targets should be modular layers around the same canonical data shape. The source reader and folder writer establish the base contract; optional targets can add publishing behavior without changing record contents.

---

## Target Model

The shared pipeline is:

```text
Wispr Flow SQLite
  -> canonical records and indexes
  -> folder export
  -> optional target sync
```

The folder export is the base target because every remote target still needs a concrete set of files to publish.

## Supported And Future Targets

| Target | Status | Description |
| --- | --- | --- |
| Folder | Supported base design | Write files to a specified local folder. |
| Cloud-synced folder | Supported by folder export | User chooses a Dropbox, iCloud Drive, Google Drive, or OneDrive folder. |
| GitHub through Git | Planned/optional layer | Commit and push the folder export to a Git remote. |
| S3 or object storage | Future extension | Upload the canonical files to a bucket or object store. |

## Target Boundary

An export target can decide where files go after the canonical folder export exists. It should not redefine:

- `metadata.json`,
- record directory naming,
- `indexes/history.jsonl`,
- `indexes/dictionary.jsonl`,
- `manifest.json`,
- run report shape.

That keeps downstream consumers independent of the sync provider.

## Future Target Requirements

A future remote target should define:

- how credentials are configured,
- which files are uploaded,
- whether deleted local files are removed remotely,
- how retries and partial failures are reported,
- whether the target can validate remote file hashes.

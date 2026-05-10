---
covers: The code paths that read Wispr Flow data and write canonical WisprSync export records.
concepts: [export-pipeline, records, indexes]
design_refs: [10-system-design/10-data-structure/20-wisprsync-output-shape.md, 10-system-design/20-exporting/10-folder-export.md]
code-ref: wisprsync/
type: overview
---

# Export Pipeline: Overview

The export pipeline is responsible for turning read-only Wispr Flow SQLite rows into the canonical `data/` tree. It owns source selection, preflight collision checks, row-to-record normalization, atomic record writes, index generation, manifest writing, run reports, and validation entry points.

---

## File Tree

```text
wisprsync/
├── cli/                        CLI parser and command functions
├── core/                       Shared config, constants, paths, and errors
├── source/                     Source discovery, SQLite access, and History selection
├── export/                     Export orchestration, metadata, records, media, and indexes
├── support/                    Filesystem, hash, JSON, and time helpers
└── validate/                   Exported data folder validation
```

## Section Scope

### What This Section Owns

- The current code path from CLI command to exported files.
- The mapping from selected source rows to metadata, media, transcript files, and JSONL index rows.
- The update semantics implemented through source hashes and existing record indexes.
- Validation checks against the generated data folder.

### What This Section Does Not Own

- The design-level meaning of the data structure.
- User-facing setup goals and local configuration policy.
- Git commit, push, or repository sync behavior.

## Architecture

`./bin/sync` and `./bin/setup` are thin shell wrappers. They change into the repository root and execute `python3 -m wisprsync`, which enters `wisprsync/cli/main.py`.

Export flow:

```text
bin/sync
└── python3 -m wisprsync sync
    └── wisprsync.cli.commands.command_sync()
        ├── wisprsync.export.runner.command_export()
        │   ├── load config and choose source
        │   ├── create SQLite snapshot or immutable read fallback
        │   ├── preflight source and existing records
        │   ├── build/write records
        │   ├── write indexes and manifest
        │   └── write run report
        └── wisprsync.validate.runner.command_validate()
```

## Child Nodes

### [Source To Record Mapping](10-source-to-record-mapping.md)

Documents the implementation details that map a `History` row to `metadata.json`, transcript files, media files, JSONL index rows, and change detection hashes.

---
covers: How the WisprSync codebase implements setup, export, validation, and repo-local data operations.
concepts: [implementation, exporter, validation, setup]
design_refs: [10-system-design/10-data-structure/20-wisprsync-output-shape.md, 10-system-design/20-exporting/10-folder-export.md]
type: overview
---

# Implementation

The implementation layer maps the design contracts onto the current Python package and repo-local shell commands. Use it when changing how WisprSync discovers the source database, exports records, writes indexes, records run reports, or validates the `data/` folder.

---

## File Tree

```text
20-implementation/
├── 00-overview.md              (this file)
├── 10-export-pipeline/         Source reading, record writing, indexing, and validation
└── 99-appendix/                Operational setup and repo-local command docs
```

## Architecture

Repo-local commands in `bin/` call `python3 -m wisprsync`. The CLI layer resolves commands and options, the command layer resolves config, the export runner snapshots or reads the source SQLite database, and the record helpers normalize each `History` row into metadata, files, indexes, and run reports.

The current implementation is split into package sections: `wisprsync/cli/` for command parsing and command functions, `wisprsync/core/` for config/constants/path/error primitives, `wisprsync/source/` for discovery and SQLite access, `wisprsync/export/` for export orchestration and record/index helpers, `wisprsync/support/` for shared filesystem/hash/JSON/time helpers, and `wisprsync/validate/` for data-folder checks.

## Sections

### [Export Pipeline](10-export-pipeline/00-overview.md)

Documents how source rows become record directories, JSON metadata, JSONL indexes, manifests, and run reports.

### [Appendix](99-appendix/00-overview.md)

Documents operational setup, local configuration, source discovery, and repo-local command expectations.

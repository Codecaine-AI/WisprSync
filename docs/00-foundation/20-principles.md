---
covers: The core principles that guide WisprSync as a local data ownership tool.
concepts: [principles, ownership, local-first]
depends-on: [00-foundation/10-backstory.md]
---

# Principles

WisprSync is guided by a small set of principles: local data ownership, transparent export formats, and explicit user control over where exported data goes.

---

## Data Ownership

If transcript data is already on the user's device, the user should be able to inspect it, back it up, analyze it, and move it into their own workflows.

## Local First

The base export path writes to a folder the user controls.
Cloud sync, Git sync, or future remote targets should layer on top of that folder export instead of replacing it.

## Transparent Formats

The export should use plain files and documented structures: JSON, JSONL, text files, WAV audio, PNG screenshots, manifests, and run reports.

## Explicit Sync

WisprSync should not commit, push, upload, or delete exported data unless the user explicitly chooses that behavior.

## Safe Defaults

The exporter should avoid raw app folders, cookies, sessions, caches, telemetry files, and local machine config.
The canonical export should contain transcript data and related artifacts, not private application runtime state.

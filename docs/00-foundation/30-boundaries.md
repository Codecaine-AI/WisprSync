---
covers: What WisprSync is and is not responsible for.
concepts: [boundaries, non-affiliation, safety]
depends-on: [00-foundation/10-backstory.md, 00-foundation/20-principles.md]
---

# Boundaries

WisprSync is a local exporter for data already present on the user's machine. It is not an official Wispr Flow feature, not a cloud API client, and not a restore tool.

---

## Not Affiliated With Wispr Flow

WisprSync is not affiliated with, endorsed by, or supported by Wispr Flow.
Users run it at their own risk.

## Not A Wispr Flow Restore Tool

WisprSync exports data out of local Wispr Flow storage.
It does not write data back into Wispr Flow.

## Not A Raw App Data Backup

WisprSync should not treat the full Wispr Flow application support folder as the export.
Cookies, sessions, caches, telemetry folders, and SQLite source snapshots are outside the canonical export.

## Not Automatic Publishing

The base export writes to a folder.
Git commits, GitHub pushes, object storage uploads, or other remote sync behaviors should be explicit layers.

## Not A Permanent Schema Contract

Wispr Flow can change its local storage paths or SQLite schema.
The dated local storage reference in `.codex/skills/wisprsync/reference/` should be updated when that happens.

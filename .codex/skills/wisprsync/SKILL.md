---
name: wisprsync
description: Set up, operate, and troubleshoot a local WisprSync repository that exports Wispr Flow transcript data into a canonical searchable data folder. Use when asked to initialize, configure, sync, validate, troubleshoot, or schedule WisprSync.
---

# WisprSync

Use this skill as the setup and troubleshooting wizard for a WisprSync fork or clone.

WisprSync is repo-local first: do not require a global `wisprsync`, `npx`, or
`pipx` install for normal use. Prefer commands from the repository root.

## Workflow

1. Confirm the current directory is the WisprSync repo root.
2. If `.wisprsync/config.json` is missing, set up the repo:
   - Run `./bin/setup`.
   - Follow `docs/20-implementation/99-appendix/10-setup-workflow.md` when troubleshooting or extending setup behavior.
3. Confirm the selected source database is the user's Wispr Flow database.
4. Confirm the output directory, usually `data`.
5. Run `./bin/sync` to export and validate.
6. Summarize counts from `data/manifest.json` and the latest run report.

## References

Read only the reference needed for the task:

- `docs/20-implementation/99-appendix/10-setup-workflow.md`: source discovery, local config, repo commands, scheduling.
- `docs/10-system-design/10-data-structure/10-wispr-flow-source-shape.md`: Wispr Flow source tables, fields, media, and dictionary data.
- `docs/10-system-design/10-data-structure/20-wisprsync-output-shape.md`: exported files, JSON objects, indexes, manifest, and run reports.
- `docs/10-system-design/20-exporting/10-folder-export.md`: default folder export flow, repeat sync behavior, hashes, and safety checks.
- `docs/10-system-design/20-exporting/20-github-git-export.md`: optional Git/GitHub sync layer.
- `.codex/skills/wisprsync/reference/wispr-flow-local-storage.md`: dated reference for likely Wispr Flow macOS storage paths and observed SQLite shape.

## Local Storage Refresh Workflow

When asked to refresh or verify Wispr Flow local storage assumptions, act like a self-healing discovery agent.
Do not rely on one fixed script as the source of truth.
Use the dated reference as the starting hypothesis, inspect the current machine, then update the reference and any affected docs/code.

Preferred workflow:

1. Read `.codex/skills/wisprsync/reference/wispr-flow-local-storage.md`.
2. Find the installed Wispr Flow app bundle.
   - Prefer `/Applications/Wispr Flow.app`.
   - Also check `$HOME/Applications` and Spotlight results if needed.
3. Read the app version from `Contents/Info.plist`.
   - Use `CFBundleShortVersionString`.
   - Use `CFBundleVersion`.
4. Check likely SQLite database candidates.
   - `~/Library/Application Support/Wispr Flow/flow.sqlite`
   - `~/Library/Application Support/Flow/flow.sqlite`
5. Use read-only SQLite inspection.
   - List tables.
   - Count `History` rows.
   - Read min/max `History.timestamp`.
   - Inspect `History` columns and important field presence.
   - Inspect `Dictionary` columns if present.
   - Sample top `History.appVersion` values to separate historical row versions from the installed app version.
6. If expected candidates fail, search standard macOS app data locations for `wispr`, `flow`, and `whisper`.
7. Update `.codex/skills/wisprsync/reference/wispr-flow-local-storage.md`.
   - Update `last_verified_on`.
   - Update platform and app version metadata.
   - Update likely paths, observed tables, fields, and verification snapshot.
8. If source concepts changed, update `docs/10-system-design/10-data-structure/10-wispr-flow-source-shape.md`.
9. If discovery behavior changed, update source discovery code and setup docs.
10. Run setup/export/validation after changes.

Useful commands:

```sh
/usr/libexec/PlistBuddy -c 'Print :CFBundleShortVersionString' -c 'Print :CFBundleVersion' '/Applications/Wispr Flow.app/Contents/Info.plist'
sqlite3 -readonly "$DB" '.tables'
sqlite3 -readonly "$DB" 'select count(*) from History;'
sqlite3 -readonly "$DB" 'select min(timestamp), max(timestamp), count(*) from History;'
sqlite3 -readonly "$DB" 'pragma table_info(History);'
sqlite3 -readonly "$DB" 'pragma table_info(Dictionary);'
sqlite3 -readonly "$DB" "select appVersion, count(*) from History where appVersion is not null and appVersion != '' group by appVersion order by count(*) desc limit 20;"
```

## Source Discovery

Expected macOS candidates from the local audit:

```text
~/Library/Application Support/Wispr Flow/flow.sqlite
~/Library/Application Support/Flow/flow.sqlite
```

Use a readable database with a `History` table. If multiple candidates are
valid, prefer the one with the most `History` rows and tell the user.
If these candidates stop working, use
`.codex/skills/wisprsync/reference/wispr-flow-local-storage.md` to re-discover
the current Wispr Flow storage layout and update the reference.

## Export Shape

Each record exports up to these files:

```text
metadata.json
raw_transcript.txt
formatted_transcript.txt
audio.wav
screenshot.png
```

Files may be absent when the source row has no corresponding value. Dictionary
export refreshes to the latest current state on each sync.

## Guardrails

- Do not commit raw Wispr Flow app data, cookies, sessions, caches, or SQLite
  source snapshots.
- Do not commit `.wisprsync/config.json`.
- Do not commit or push unless the user explicitly asks.
- Keep implementation repo-local and Python-based for v1 (`wisprsync/`
  package, with `python3 -m wisprsync` as the internal command interface).

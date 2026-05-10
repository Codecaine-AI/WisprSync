---
name: wisprsync
description: Set up, operate, and troubleshoot a local WisprSync repository that exports Wispr Flow transcript data into a canonical searchable data folder. Use when asked to initialize, configure, sync, validate, troubleshoot, or schedule WisprSync.
---

# WisprSync

Use this skill as the setup and troubleshooting wizard for a WisprSync fork or clone.

WisprSync is repo-local first: do not require a global `wisprsync`, `npx`, or
`pipx` install for normal use. Prefer commands from the repository root.

## Workflow

When this skill runs, sync and the rest can be one shot — but **setup must be agent-driven with explicit gates**, because `./bin/setup`'s interactive prompts only work when a human runs them in a real TTY. Agent shells are not TTYs, so the prompts are silently skipped and the user is never asked where their data should go. Use the gated flow below instead, then call setup non-interactively with all answers as flags.

1. Confirm the current directory is the WisprSync repo root.
2. If `.wisprsync/config.json` exists, ask the user whether to reuse it or reconfigure. Skip to step 7 if reusing.
3. **Run setup as a gated agent flow** (each gate = one explicit user question; never invent answers):
   1. **Source gate.** Run `python3 -m wisprsync doctor` to list discovered Wispr Flow databases with `History` row counts. Show the candidates to the user and ask which one to use, accepting a custom path. If discovery returns nothing, ask the user for an explicit path.
   2. **Output gate.** Propose `../wispr_sync` (sibling of the repo) as the default. Ask the user to confirm or supply their own path. If their answer resolves inside the WisprSync repo, warn explicitly that exported data should not be committed and re-confirm before proceeding.
   3. **Screenshots gate.** Ask whether to include screenshots (default yes).
   4. **Schedule gate.** Ask whether to install the daily midnight LaunchAgent (default no).
   5. **Review gate.** Show source, resolved output, screenshots, schedule, and config path back to the user. Ask for confirmation before writing anything.
4. Only after every gate is answered, invoke setup non-interactively with all values passed as flags:
   ```sh
   ./bin/setup --yes \
     --source "<answer>" \
     --output "<answer>" \
     [--no-screenshots] [--schedule] [--allow-unsafe-output]
   ```
   Pass `--allow-unsafe-output` only when the user explicitly confirmed a repo-local output path at the output gate.
5. If any gate is denied or the user aborts, do not run `./bin/setup`; report what was skipped.
6. See `docs/20-implementation/99-appendix/10-setup-workflow.md` for source discovery rules, safety constraints, and the full CLI surface.
7. Run `./bin/sync` to export and validate.
8. Summarize counts from the configured output's `manifest.json` and the latest run report.

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

---
covers: How WisprSync local setup discovers the source database, writes config, and exposes repo-local commands.
concepts: [setup, discovery, config, commands]
---

# Setup Workflow

WisprSync is repo-local first. A user can fork or clone the repo, open it with an agent, and run setup from the repository root without installing a global package.

---

## Local Config

Machine-local config is written to:

```text
.wisprsync/config.json
```

Example:

```json
{
  "schema_version": 1,
  "source_database": "/Users/example/Library/Application Support/Wispr Flow/flow.sqlite",
  "output_directory": "/Users/example/Documents/wispr_sync",
  "include_screenshots": true,
  "schedule": {
    "enabled": false,
    "provider": "launchd",
    "local_time": "00:00"
  }
}
```

`.wisprsync/config.json` stays ignored by Git.

## Source Discovery

Known macOS candidates from the dated Wispr Flow local storage reference:

```text
~/Library/Application Support/Wispr Flow/flow.sqlite
~/Library/Application Support/Flow/flow.sqlite
```

The reference lives at:

```text
.codex/skills/wisprsync/reference/wispr-flow-local-storage.md
```

Update that reference if Wispr Flow changes its app storage location or SQLite schema.

Discovery rules:

1. Expand `~` to the current user's home directory.
2. Keep candidates that exist and are readable SQLite databases.
3. Verify each candidate has a `History` table.
4. Count `History` rows for valid candidates.
5. Prefer the valid candidate with the most `History` rows.
6. Show the chosen path to the user or mention it in the setup summary.
7. Allow an override if the user gives an explicit path.

Useful read-only checks:

```sh
sqlite3 -readonly "$DB" '.tables'
sqlite3 -readonly "$DB" 'select count(*) from History;'
```

If the database is copied and reports locked, immutable URI mode can inspect it:

```sh
sqlite3 "file:$DB?mode=ro&immutable=1" 'select count(*) from History;'
```

For the live app database, SQLite backup APIs are preferred over reading from an inconsistent direct copy.

## Repo Commands

Expected repo-local commands:

```sh
./bin/setup
./bin/sync
```

`./bin/setup`:

- prints the repository root and target `.wisprsync/config.json` path,
- discovers candidate source databases and shows their paths and `History` row counts,
- asks the user which source database to use, while accepting a custom path,
- asks where exported files should go before any sync runs,
- suggests `../wispr_sync` as the default output location,
- resolves and displays the exact output path,
- asks before using a destination that does not exist,
- warns before using a repo-local output path and requires explicit confirmation,
- keeps `.wisprsync/` and `.wisprsync-cache/` blocked,
- asks whether to include screenshots and whether to install a daily schedule,
- defaults screenshots to enabled,
- shows a final review of source, output, screenshots, schedule, and config path,
- writes `.wisprsync/config.json` only after `Write this config? [Y/n]` is accepted.

Automation is stricter than interactive setup. Noninteractive setup, including
`--yes`, requires `--output`; it never silently infers an output directory.
Scripted developer workflows can still pass `--allow-unsafe-output`, but an
output path that already exists as a file remains non-overridable.

`./bin/sync`:

- runs export,
- runs validation.

`./bin/schedule install`:

- writes a macOS LaunchAgent,
- creates a private no-pip `.wisprsync/runner-venv` runtime,
- creates a dedicated `.wisprsync/WisprSync Runner.app` launcher,
- runs that dedicated launcher from the LaunchAgent,
- defaults to daily at 00:00 local time.

Internally, these call the package module:

```sh
python3 -m wisprsync setup
python3 -m wisprsync sync
python3 -m wisprsync export
python3 -m wisprsync validate
python3 -m wisprsync schedule install
python3 -m wisprsync doctor
```

Implementation code stays in package modules under `wisprsync/`.

## Scheduling

Scheduling should call repo-local commands from this repository, for example:

```sh
cd /path/to/WisprSync && ./bin/sync
```

On macOS, `launchd` is the preferred scheduler for user-session reliability. The scheduler installs a user LaunchAgent named `com.codecaine.wispr_sync_runner` that runs `.wisprsync/WisprSync Runner.app/Contents/MacOS/wisprsync-runner` at midnight.

The dedicated runner app exists so macOS privacy access can be granted to
WisprSync's local scheduled runner instead of granting Full Disk Access to a
shared Python interpreter. The runner app executes the private
`.wisprsync/runner-venv/bin/python` copy created during schedule installation.

See [macOS Scheduler Permissions](20-macos-scheduler-permissions.md) for the
implementation details, runtime paths, verification commands, and failure-mode
notes.

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
  "output_directory": "data",
  "include_screenshots": true
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

- discovers the source database,
- chooses or confirms the output directory,
- defaults output to `data`,
- defaults screenshots to enabled,
- writes `.wisprsync/config.json`.

`./bin/sync`:

- runs export,
- runs validation,
- does not commit or push unless explicitly requested.

Internally, these call the package module:

```sh
python3 -m wisprsync setup
python3 -m wisprsync sync
python3 -m wisprsync export
python3 -m wisprsync validate
python3 -m wisprsync doctor
```

Implementation code stays in package modules under `wisprsync/`.

## Scheduling

Scheduling should call repo-local commands from this repository, for example:

```sh
cd /path/to/WisprSync && ./bin/sync
```

On macOS, `launchd` is the preferred scheduler for user-session reliability. A scheduling helper can be added separately; normal export behavior does not depend on scheduled execution.

---
covers: How the macOS scheduled sync runner is installed, how it executes, and how privacy permissions are scoped.
concepts: [macos, launchd, permissions, scheduler, runner]
design_refs: [10-system-design/20-exporting/10-folder-export.md]
type: implementation
---

# macOS Scheduler Permissions

WisprSync's scheduled macOS sync uses a dedicated local runner instead of a
shared Python interpreter. This keeps the permission target narrow when macOS
privacy controls gate access to the Wispr Flow database and the configured
export folder.

---

## Problem

The scheduled job needs to read the Wispr Flow SQLite database and write the
configured export folder. On this machine, those paths are:

```text
~/Library/Application Support/Wispr Flow/flow.sqlite
~/Library/CloudStorage/Dropbox/wispr_sync
```

When `launchd` runs a headless job, macOS privacy controls can deny access even
when the same command works from an interactive terminal. Granting Full Disk
Access to a global Python executable would make every script run by that Python
binary inherit broad access, which is too large a trust target for this tool.

## Runtime Shape

`python3 -m wisprsync schedule install` creates three local scheduler artifacts:

```text
~/Library/LaunchAgents/com.codecaine.wispr_sync_runner.plist
.wisprsync/WisprSync Runner.app/
.wisprsync/runner-venv/
```

The LaunchAgent runs only the dedicated app bundle executable:

```text
.wisprsync/WisprSync Runner.app/Contents/MacOS/wisprsync-runner
```

That executable is a small shell script generated during install. It changes to
the repository root and executes the private runtime:

```sh
exec .wisprsync/runner-venv/bin/python -m wisprsync sync "$@"
```

The private runtime is created with Python's standard `venv` module using
`with_pip=False` and `symlinks=False`. This creates a local Python copy for the
scheduled runner without installing package-management tooling into that
runtime.

## Permission Boundary

The intended permission target is:

```text
.wisprsync/WisprSync Runner.app
```

If macOS blocks the scheduled job, grant privacy access to that app bundle, not
to `/usr/bin/python3`, Xcode Python, Anaconda Python, or another shared
interpreter.

This does not create perfect path-level sandboxing. macOS privacy controls are
still process based. The improvement is that the process receiving access is a
repo-local WisprSync runner whose only generated command path is `wisprsync
sync`, backed by a private runtime inside `.wisprsync/`.

## Install Flow

Schedule installation is implemented in `wisprsync/sync/schedule.py`.

The install sequence is:

1. Create `.wisprsync/runner-venv` if its Python executable is missing.
2. Generate `.wisprsync/WisprSync Runner.app/Contents/Info.plist`.
3. Generate `.wisprsync/WisprSync Runner.app/Contents/MacOS/wisprsync-runner`.
4. Write `~/Library/LaunchAgents/com.codecaine.wispr_sync_runner.plist`.
5. Unload any existing job for the same label.
6. Load the new LaunchAgent.

The LaunchAgent keeps the existing schedule contract: daily at `00:00` local
time, stdout to `.wisprsync/schedule.out.log`, and stderr to
`.wisprsync/schedule.err.log`.

## Verification

After install, verify the LaunchAgent target:

```sh
plutil -p ~/Library/LaunchAgents/com.codecaine.wispr_sync_runner.plist
```

The `ProgramArguments` entry should point at:

```text
.wisprsync/WisprSync Runner.app/Contents/MacOS/wisprsync-runner
```

Kick the job manually:

```sh
launchctl kickstart -k gui/$(id -u)/com.codecaine.wispr_sync_runner
```

Then check logs and status:

```sh
tail -n 80 .wisprsync/schedule.err.log
tail -n 30 .wisprsync/schedule.out.log
launchctl list com.codecaine.wispr_sync_runner
```

A healthy run has `LastExitStatus = 0`, no permission traceback in
`schedule.err.log`, and a normal sync summary in `schedule.out.log`.

## Failure Modes

If the run fails with `unable to open database file`, macOS probably denied
access to the Wispr Flow source database.

If the run fails with `Operation not permitted` while writing under the output
folder, macOS probably denied access to the export target.

In either case, the first permission target to try is the dedicated runner app:

```text
.wisprsync/WisprSync Runner.app
```

After granting access, kick the LaunchAgent again and confirm the next run
report is successful.

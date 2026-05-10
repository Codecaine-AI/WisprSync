---
covers: The optional Git/GitHub export mode that syncs the folder export through a repository remote.
concepts: [git, github, export-mode, cloud-sync]
depends-on: [10-system-design/20-exporting/10-folder-export.md]
---

# GitHub Git Export

GitHub Git export is a sync layer on top of folder export. WisprSync first writes the normal folder export, then a separate Git step can commit and push that output to a remote repository.

---

## Role

This mode uses GitHub as the cloud sync provider. It is useful when the user wants version history, diffs, private repository backup, or agent-friendly access to exported transcript data.

It should not be part of the default folder export. A normal export should never surprise the user with a commit or push.

## Flow

1. Run the normal folder export.
2. Validate the exported folder.
3. Stage the intended export files.
4. Commit with a generated export message.
5. Push to the configured remote.

The Git layer should fail independently. A failed push should not make the local folder export invalid.

## Boundaries

The Git layer owns:

- repository status checks,
- staging policy,
- commit message generation,
- push behavior,
- reporting Git failures.

The Git layer does not own:

- reading Wispr Flow SQLite data,
- shaping records,
- writing metadata and media files,
- generating indexes, manifests, or run reports.

## Default Policy

Git sync should be explicit. A future command might look like:

```sh
./bin/git-sync
```

or:

```sh
python3 -m wisprsync git-sync
```

The base `./bin/sync` command should remain a folder export and validation command unless the user explicitly opts into Git behavior.

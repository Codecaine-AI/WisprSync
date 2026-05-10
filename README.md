# WisprSync

WisprSync exports your local Wispr Flow transcript data into a folder you control.

It is built for people who want direct access to their own transcript history, audio files, metadata, and indexes without manually exporting one item at a time.

## Unofficial Project

WisprSync is an independent, unofficial project. 

It is not affiliated with, endorsed by, sponsored by, or supported by Wispr AI, Inc. or Wispr Flow.

`Wispr` and `Wispr Flow` are trademarks or product names of their respective owners. They are used here only to identify the application whose local data this tool helps a user export from their own machine.

Use it at your own risk.

It reads local application data from your machine, and the exported data can contain sensitive transcripts, app context, URLs, screenshots, and audio.

## Why This Exists

Wispr Flow has a per-transcript export path, but no simple full data export workflow.

WisprSync makes that local data visible and portable by writing it into a documented folder structure with records, metadata, text files, media files, indexes, a manifest, and run reports.

The goal is data ownership

If the data is on your machine, you should be able to inspect it, back it up, analyze it, and move it into whatever workflow you prefer.

The longer project backstory is in [docs/00-foundation/10-backstory.md](docs/00-foundation/10-backstory.md).

## Export Modes

The base export mode writes to a folder you specify.

The easiest sync setup is to choose a folder already handled by Dropbox, iCloud Drive, Google Drive, OneDrive, or a similar file sync tool.

Git/GitHub sync is a separate optional layer: export to a folder first, then commit and push if you explicitly choose that workflow.

## Prerequisite

WisprSync depends on Wispr Flow storing transcript data locally.

In Wispr Flow, go to `Settings > Data and Privacy > Local data storage` and choose `Store data locally`.

If local data storage is disabled, WisprSync will not have local transcript data to export.

![Wispr Flow Data and Privacy settings showing Local data storage set to Store data locally](docs/assets/wispr-flow-local-data-storage.png)

## Quick Start

The preferred setup path is to open this repository with Codex and ask it to use the local WisprSync skill:

```text
Use the WisprSync skill to set this repository up on my computer, then run an initial sync and summarize the manifest counts.
```

The skill guides Codex through the machine-local steps: confirm this repo root, discover the Wispr Flow SQLite database, write `.wisprsync/config.json`, run `./bin/sync`, validate the export, and summarize the latest run. This is preferred because the correct source database and output folder are local to each computer.

From the repo root:

```sh
./bin/setup
./bin/sync
```

Useful internal commands:

```sh
python3 -m wisprsync setup
python3 -m wisprsync sync
python3 -m wisprsync export
python3 -m wisprsync validate
python3 -m wisprsync doctor
```

Local machine config is written to:

```text
.wisprsync/config.json
```

That file should stay local and ignored by Git.

## Output

By default, WisprSync writes to `data/` unless configured otherwise.

```text
data/
├── manifest.json
├── indexes/
│   ├── history.jsonl
│   ├── dictionary.jsonl
│   └── runs.jsonl
├── records/
│   └── YYYY/MM/DD/{timestamp}_{transcriptEntityId}/
│       ├── metadata.json
│       ├── raw_transcript.txt
│       ├── formatted_transcript.txt
│       ├── audio.wav
│       └── screenshot.png
└── runs/
    └── YYYY/MM/DD/{run_id}.json
```

Files are omitted when the source row does not contain the corresponding value.

## Safety Notes

- Do not commit raw Wispr Flow app folders, cookies, sessions, caches, or SQLite source snapshots.
- Do not commit `.wisprsync/config.json`.
- WisprSync blocks unsafe output paths by default, including paths inside the
  source database directory, Wispr Flow app data, the repo root, or private
  `.wisprsync` state. Use `--allow-unsafe-output` only for intentional expert
  workflows.
- Be careful publishing exported `data/`; it may contain private transcripts, URLs, screenshots, and audio.
- Prefer a private repo or a private cloud-synced folder for personal exports.

## Documentation

Start at [docs/00-overview.md](docs/00-overview.md).

Key docs:

- [Backstory](docs/00-foundation/10-backstory.md)
- [Wispr Flow Source Shape](docs/10-system-design/10-data-structure/10-wispr-flow-source-shape.md)
- [WisprSync Output Shape](docs/10-system-design/10-data-structure/20-wisprsync-output-shape.md)
- [Folder Export](docs/10-system-design/20-exporting/10-folder-export.md)
- [GitHub Git Export](docs/10-system-design/20-exporting/20-github-git-export.md)
- [Setup Workflow](docs/20-implementation/99-appendix/10-setup-workflow.md)

## License

WisprSync is released under the [MIT License](LICENSE).

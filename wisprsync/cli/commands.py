from __future__ import annotations

import argparse
import json
import sys

from wisprsync.core.config import choose_source, load_config, write_config
from wisprsync.core.constants import SCHEMA_VERSION
from wisprsync.core.paths import config_path, repo_root, resolve_output
from wisprsync.export.runner import command_export
from wisprsync.source.discovery import discover_sources
from wisprsync.validate.runner import command_validate


def command_setup(args: argparse.Namespace) -> int:
    root = repo_root()
    source = choose_source(args.source)
    output = args.output or "data"
    include_screenshots = not args.no_screenshots

    if sys.stdin.isatty() and not args.yes:
        print(f"Discovered source database: {source}")
        reply = input("Use this source? [Y/n] ").strip().lower()
        if reply in {"n", "no"}:
            override = input("Source database path: ").strip()
            source = choose_source(override)
        out_reply = input(f"Output directory [{output}]: ").strip()
        if out_reply:
            output = out_reply
        shot_reply = input("Include screenshots? [Y/n] ").strip().lower()
        include_screenshots = shot_reply not in {"n", "no"}

    config = {
        "schema_version": SCHEMA_VERSION,
        "source_database": str(source.expanduser().resolve()),
        "output_directory": output,
        "include_screenshots": include_screenshots,
    }
    write_config(root, config)
    print(f"Wrote {config_path(root)}")
    print(f"Source: {config['source_database']}")
    print(f"Output: {resolve_output(root, output)}")
    print(f"Include screenshots: {include_screenshots}")
    return 0


def command_sync(args: argparse.Namespace) -> int:
    export_status = command_export(args)
    if export_status != 0 or args.dry_run:
        return export_status
    validate_args = argparse.Namespace(output=args.output)
    return command_validate(validate_args)


def command_doctor(args: argparse.Namespace) -> int:
    root = repo_root()
    print(f"Repo root: {root}")
    config = load_config(root)
    if config:
        print(f"Config: {config_path(root)}")
        print(json.dumps(config, indent=2, sort_keys=True))
    else:
        print("Config: missing")
    discovered = discover_sources()
    if not discovered:
        print("Discovered sources: none")
    else:
        print("Discovered sources:")
        for item in discovered:
            print(f"- {item['path']} ({item['history_rows']} History rows)")
    return 0

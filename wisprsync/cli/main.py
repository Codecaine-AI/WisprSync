from __future__ import annotations

import argparse
import sys

from wisprsync.cli.commands import command_doctor, command_setup, command_sync
from wisprsync.core.errors import WisprSyncError
from wisprsync.export.runner import command_export
from wisprsync.validate.runner import command_validate


def add_export_like_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--source")
    parser.add_argument("--output")
    parser.add_argument("--include-screenshots", action="store_true")
    parser.add_argument("--no-screenshots", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="wisprsync", description="Repo-local Wispr Flow data exporter")
    subparsers = parser.add_subparsers(dest="command", required=True)

    setup = subparsers.add_parser("setup")
    setup.add_argument("--source")
    setup.add_argument("--output", default="data")
    setup.add_argument("--yes", action="store_true")
    setup.add_argument("--no-screenshots", action="store_true")
    setup.set_defaults(func=command_setup)

    export = subparsers.add_parser("export")
    add_export_like_args(export)
    export.set_defaults(func=command_export)

    sync = subparsers.add_parser("sync")
    add_export_like_args(sync)
    sync.set_defaults(func=command_sync)

    validate = subparsers.add_parser("validate")
    validate.add_argument("--output")
    validate.set_defaults(func=command_validate)

    doctor = subparsers.add_parser("doctor")
    doctor.set_defaults(func=command_doctor)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except WisprSyncError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

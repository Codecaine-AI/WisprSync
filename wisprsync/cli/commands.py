from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from wisprsync.core.errors import WisprSyncError
from wisprsync.core.config import choose_source, load_config, write_config
from wisprsync.core.constants import SCHEMA_VERSION
from wisprsync.core.paths import config_path, repo_root, resolve_output
from wisprsync.core.safety import is_same_or_child, unsafe_output_reasons, validate_export_paths
from wisprsync.export.runner import command_export
from wisprsync.source.discovery import discover_sources
from wisprsync.sync.cleanup import cleanup_repo_data
from wisprsync.sync.schedule import install_launch_agent, launch_agent_status, remove_launch_agent
from wisprsync.validate.runner import command_validate

DEFAULT_OUTPUT_DIRECTORY_NAME = "wispr_sync"


def _prompt_source(source_arg: str | None) -> Path:
    if source_arg:
        source = choose_source(source_arg)
        print(f"Source database: {source}")
        reply = input("Use this source? [Y/n] ").strip().lower()
        if reply not in {"n", "no"}:
            return source

    discovered = discover_sources()
    if discovered:
        print("Discovered Wispr Flow databases:")
        for index, item in enumerate(discovered, start=1):
            print(f"  {index}. {item['path']} ({item['history_rows']} History rows)")
    else:
        print("No Wispr Flow database was discovered automatically.")

    while True:
        default = "1" if discovered else ""
        suffix = f" [{default}]" if default else ""
        reply = input(f"Source database number or path{suffix}: ").strip()
        reply = reply or default
        if reply.isdigit() and discovered:
            index = int(reply)
            if 1 <= index <= len(discovered):
                return choose_source(discovered[index - 1]["path"])
        if reply:
            return choose_source(reply)
        print("Enter a source database path.")


def _prompt_output(root: Path) -> str:
    default_output = str(root.parent / DEFAULT_OUTPUT_DIRECTORY_NAME)
    print("Choose where WisprSync should write exported transcripts.")
    output = input(f"Output directory [{default_output}]: ").strip()
    return output or default_output


def _confirm(prompt: str, default: bool = True) -> bool:
    suffix = "[Y/n]" if default else "[y/N]"
    reply = input(f"{prompt} {suffix} ").strip().lower()
    if not reply:
        return default
    return reply in {"y", "yes"}


def _validate_interactive_output(root: Path, source: Path, output: Path) -> None:
    reasons = unsafe_output_reasons(root, source, output)
    repo_local = is_same_or_child(output, root)
    if reasons:
        raise WisprSyncError("unsafe output path: " + "; ".join(reasons))
    if output == root.expanduser().resolve():
        raise WisprSyncError("unsafe output path: output path is the WisprSync repository root")

    if not output.exists():
        if not _confirm("Output directory does not exist. Create/use this location?", default=True):
            raise WisprSyncError("setup aborted before writing config")
    elif output.is_file():
        raise WisprSyncError("output path already exists as a file")

    if repo_local:
        print("Warning: this output directory is inside the WisprSync repository.")
        print("Large exported data can clutter the repo and should not be committed.")
        if not _confirm("Use this repo-local output directory?", default=False):
            raise WisprSyncError("setup aborted before writing config")


def _print_setup_review(config: dict[str, object], resolved_output: Path, root: Path) -> None:
    schedule = config["schedule"]
    assert isinstance(schedule, dict)
    print("")
    print("Review setup:")
    print(f"  Source database: {config['source_database']}")
    print(f"  Output directory: {resolved_output}")
    print(f"  Include screenshots: {config['include_screenshots']}")
    print(f"  Schedule: {'launchd daily at 00:00 local time' if schedule.get('enabled') else 'disabled'}")
    print(f"  Config path: {config_path(root)}")


def command_setup(args: argparse.Namespace) -> int:
    root = repo_root()
    output = args.output
    schedule_enabled = bool(args.schedule)
    include_screenshots = not args.no_screenshots

    if sys.stdin.isatty() and not args.yes:
        print(f"Repo root: {root}")
        print(f"Config path: {config_path(root)}")
        source = _prompt_source(args.source)
        output = _prompt_output(root)
        resolved_output = resolve_output(root, output)
        print(f"Resolved output directory: {resolved_output}")
        _validate_interactive_output(root, source, resolved_output)
        include_screenshots = _confirm("Include screenshots?", default=True)
        schedule_enabled = _confirm("Install daily midnight schedule?", default=False)
    else:
        if not args.source or not output:
            missing = ", ".join(name for name, val in (("--source", args.source), ("--output", output)) if not val)
            raise WisprSyncError(
                f"non-interactive setup requires {missing}; "
                "agents must collect these from the user via the gated flow in "
                ".codex/skills/wisprsync/SKILL.md before invoking setup"
            )
        source = choose_source(args.source)

    resolved_output = resolve_output(root, output)
    allow_unsafe_output = getattr(args, "allow_unsafe_output", False)
    interactive = sys.stdin.isatty() and not args.yes
    if not interactive and is_same_or_child(resolved_output, root) and not allow_unsafe_output:
        raise WisprSyncError(
            "setup output must be outside the WisprSync repository; "
            "pass --allow-unsafe-output only for intentional developer workflows"
        )
    if interactive:
        validate_export_paths(root, source, resolved_output, allow_unsafe_output=True)
    else:
        validate_export_paths(root, source, resolved_output, allow_unsafe_output)

    config = {
        "schema_version": SCHEMA_VERSION,
        "source_database": str(source.expanduser().resolve()),
        "output_directory": output,
        "include_screenshots": include_screenshots,
        "schedule": {
            "enabled": schedule_enabled,
            "provider": "launchd",
            "local_time": "00:00",
        },
    }
    if interactive:
        _print_setup_review(config, resolved_output, root)
        if not _confirm("Write this config?", default=True):
            print("Setup aborted; config was not written.")
            return 1
    write_config(root, config)
    if schedule_enabled:
        install_launch_agent(root)
    print(f"Wrote {config_path(root)}")
    print(f"Source: {config['source_database']}")
    print(f"Output: {resolved_output}")
    print(f"Include screenshots: {include_screenshots}")
    if schedule_enabled:
        print("Schedule: launchd daily at 00:00 local time")
    return 0


def command_sync(args: argparse.Namespace) -> int:
    export_status = command_export(args)
    if export_status != 0 or args.dry_run:
        return export_status
    validate_args = argparse.Namespace(output=args.output)
    validate_status = command_validate(validate_args)
    if validate_status != 0:
        return validate_status
    return 0


def command_schedule_install(args: argparse.Namespace) -> int:
    root = repo_root()
    path = install_launch_agent(root)
    config = load_config(root)
    if config:
        config["schedule"] = {
            "enabled": True,
            "provider": "launchd",
            "local_time": "00:00",
        }
        write_config(root, config)
    print(f"Installed schedule: {path}")
    print("Runs daily at 00:00 local time")
    return 0


def command_schedule_remove(args: argparse.Namespace) -> int:
    root = repo_root()
    path = remove_launch_agent()
    config = load_config(root)
    if config:
        schedule = config.get("schedule", {})
        schedule["enabled"] = False
        schedule.setdefault("provider", "launchd")
        schedule.setdefault("local_time", "00:00")
        config["schedule"] = schedule
        write_config(root, config)
    print(f"Removed schedule: {path}")
    return 0


def command_schedule_status(args: argparse.Namespace) -> int:
    path, exists = launch_agent_status()
    print(f"Schedule plist: {path}")
    print(f"Installed: {exists}")
    return 0


def command_cleanup_repo_data(args: argparse.Namespace) -> int:
    if not args.yes and sys.stdin.isatty():
        reply = input("Remove repo-local data/ export folder? [y/N] ").strip().lower()
        if reply not in {"y", "yes"}:
            print("Cleanup skipped")
            return 0
    elif not args.yes:
        raise WisprSyncError("cleanup-repo-data requires --yes when not running interactively")
    removed = cleanup_repo_data(repo_root())
    print("Removed data/" if removed else "No repo-local data/ folder found")
    return 0


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

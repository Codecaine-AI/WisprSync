from __future__ import annotations

import argparse
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from wisprsync.cli.commands import command_setup
from wisprsync.cli.main import build_parser
from wisprsync.core.errors import WisprSyncError
from wisprsync.core.safety import ensure_child, unsafe_output_reasons, validate_export_paths


class SafetyTests(unittest.TestCase):
    def test_normal_repo_data_output_is_allowed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            source_dir = Path(tmp) / "app"
            source = source_dir / "flow.sqlite"
            output = root / "data"
            root.mkdir()
            source_dir.mkdir()
            source.touch()

            validate_export_paths(root, source, output)

    def test_rejects_source_database_overlap(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            source_dir = Path(tmp) / "Wispr Flow"
            source = source_dir / "flow.sqlite"
            root.mkdir()
            source_dir.mkdir()
            source.touch()

            blocked = [
                source,
                source_dir,
                source_dir / "export",
                Path(tmp),
            ]

            for output in blocked:
                with self.subTest(output=output):
                    with self.assertRaises(WisprSyncError):
                        validate_export_paths(root, source, output)

    def test_rejects_known_wispr_app_data_roots(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            source = Path(tmp) / "flow.sqlite"
            root.mkdir()
            source.touch()
            output = Path.home() / "Library/Application Support/Wispr Flow/export"

            reasons = unsafe_output_reasons(root, source, output)

            self.assertTrue(any("Wispr Flow app data" in reason for reason in reasons))

    def test_rejects_broad_and_private_targets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            source = Path(tmp) / "flow.sqlite"
            root.mkdir()
            source.touch()

            blocked = [
                Path("/"),
                Path.home(),
                root,
                root / ".wisprsync",
                root / ".wisprsync-cache/source-backups",
            ]

            for output in blocked:
                with self.subTest(output=output):
                    with self.assertRaises(WisprSyncError):
                        validate_export_paths(root, source, output)

    def test_resolves_symlinked_output_before_checking(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            source_dir = Path(tmp) / "app-data"
            source = source_dir / "flow.sqlite"
            link = Path(tmp) / "linked-output"
            root.mkdir()
            source_dir.mkdir()
            source.touch()
            link.symlink_to(source_dir, target_is_directory=True)

            with self.assertRaises(WisprSyncError):
                validate_export_paths(root, source, link / "export")

    def test_override_allows_unsafe_path_but_not_file_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            source_dir = Path(tmp) / "app-data"
            source = source_dir / "flow.sqlite"
            root.mkdir()
            source_dir.mkdir()
            source.touch()

            validate_export_paths(root, source, source_dir / "export", allow_unsafe_output=True)

            with self.assertRaises(WisprSyncError):
                validate_export_paths(root, source, source, allow_unsafe_output=True)

    def test_ensure_child_rejects_record_cleanup_outside_records(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            records = Path(tmp) / "data" / "records"
            inside = records / "2026/05/10/record"
            outside = Path(tmp) / "data" / "manifest.json"

            ensure_child(records, inside, "record directory")
            with self.assertRaises(WisprSyncError):
                ensure_child(records, outside, "old record directory")

    def test_cli_parser_accepts_allow_unsafe_output_for_write_commands(self) -> None:
        parser = build_parser()

        for command in ("setup", "export", "sync"):
            args = parser.parse_args([command, "--allow-unsafe-output"])
            self.assertTrue(args.allow_unsafe_output)

    def test_setup_refuses_to_write_config_for_unsafe_output_without_override(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            source_dir = Path(tmp) / "app-data"
            source = source_dir / "flow.sqlite"
            root.mkdir()
            source_dir.mkdir()
            self._create_history_db(source)
            args = argparse.Namespace(
                source=str(source),
                output=str(source_dir / "export"),
                yes=True,
                no_screenshots=False,
                allow_unsafe_output=False,
            )

            with mock.patch("wisprsync.cli.commands.repo_root", return_value=root):
                with self.assertRaises(WisprSyncError):
                    command_setup(args)

            self.assertFalse((root / ".wisprsync" / "config.json").exists())

    @staticmethod
    def _create_history_db(path: Path) -> None:
        with sqlite3.connect(path) as conn:
            conn.execute('create table "History" (transcriptEntityId text)')


if __name__ == "__main__":
    unittest.main()

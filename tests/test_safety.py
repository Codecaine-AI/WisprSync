from __future__ import annotations

import argparse
import io
import json
import sqlite3
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

from wisprsync.cli.commands import command_cleanup_repo_data, command_setup, command_sync
from wisprsync.cli.main import build_parser
from wisprsync.core.constants import HISTORY_COLUMNS
from wisprsync.core.errors import WisprSyncError
from wisprsync.sync.schedule import LABEL, render_launch_agent, runner_executable_path
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
                schedule=False,
                yes=True,
                no_screenshots=False,
                allow_unsafe_output=False,
            )

            with mock.patch("wisprsync.cli.commands.repo_root", return_value=root):
                with self.assertRaises(WisprSyncError):
                    command_setup(args)

            self.assertFalse((root / ".wisprsync" / "config.json").exists())

    def test_setup_requires_output_when_noninteractive(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            source = Path(tmp) / "app-data" / "flow.sqlite"
            root.mkdir()
            source.parent.mkdir()
            self._create_history_db(source)
            args = argparse.Namespace(
                source=str(source),
                output=None,
                schedule=False,
                yes=True,
                no_screenshots=False,
                allow_unsafe_output=False,
            )

            with mock.patch("wisprsync.cli.commands.repo_root", return_value=root):
                with self.assertRaises(WisprSyncError):
                    command_setup(args)

    def test_setup_does_not_require_sync_mode_when_noninteractive(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            source = Path(tmp) / "app-data" / "flow.sqlite"
            output = Path(tmp) / "wispr_sync"
            root.mkdir()
            source.parent.mkdir()
            self._create_history_db(source)
            args = argparse.Namespace(
                source=str(source),
                output=str(output),
                schedule=False,
                yes=True,
                no_screenshots=False,
                allow_unsafe_output=False,
            )

            with mock.patch("wisprsync.cli.commands.repo_root", return_value=root):
                self.assertEqual(command_setup(args), 0)

            config = json.loads((root / ".wisprsync" / "config.json").read_text(encoding="utf-8"))
            self.assertNotIn("sync_mode", config)
            self.assertNotIn("git", config)

    def test_interactive_setup_defaults_to_wispr_sync_name(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            source = Path(tmp) / "app-data" / "flow.sqlite"
            root.mkdir()
            source.parent.mkdir()
            self._create_history_db(source)
            args = argparse.Namespace(
                source=str(source),
                output=None,
                schedule=False,
                yes=False,
                no_screenshots=False,
                allow_unsafe_output=False,
            )
            replies = io.StringIO("\n\n\n\n\n\n\n")

            with mock.patch("wisprsync.cli.commands.repo_root", return_value=root):
                with mock.patch("sys.stdin", replies):
                    with mock.patch.object(replies, "isatty", return_value=True):
                        command_setup(args)

            config = (root / ".wisprsync" / "config.json").read_text(encoding="utf-8")
            expected_output = root.parent / "wispr_sync"
            self.assertIn(f'"output_directory": "{expected_output}"', config)
            self.assertNotIn('"sync_mode"', config)

    def test_interactive_setup_lists_discovered_sources_before_selection(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            source = Path(tmp) / "app-data" / "flow.sqlite"
            root.mkdir()
            source.parent.mkdir()
            self._create_history_db(source)
            args = argparse.Namespace(
                source=None,
                output=None,
                schedule=False,
                yes=False,
                no_screenshots=False,
                allow_unsafe_output=False,
            )
            replies = io.StringIO("\n\n\n\n\n\n\n")
            output = io.StringIO()

            with mock.patch("wisprsync.cli.commands.repo_root", return_value=root):
                with mock.patch(
                    "wisprsync.cli.commands.discover_sources",
                    return_value=[{"path": str(source), "history_rows": 12}],
                ):
                    with mock.patch("sys.stdin", replies):
                        with mock.patch("sys.stdout", output):
                            with mock.patch.object(replies, "isatty", return_value=True):
                                command_setup(args)

            self.assertIn("Discovered Wispr Flow databases:", output.getvalue())
            self.assertIn(f"1. {source} (12 History rows)", output.getvalue())
            config = json.loads((root / ".wisprsync" / "config.json").read_text(encoding="utf-8"))
            self.assertEqual(Path(config["source_database"]), source.resolve())

    def test_interactive_setup_accepts_custom_source_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            source = Path(tmp) / "custom" / "flow.sqlite"
            root.mkdir()
            source.parent.mkdir()
            self._create_history_db(source)
            args = argparse.Namespace(
                source=None,
                output=None,
                schedule=False,
                yes=False,
                no_screenshots=False,
                allow_unsafe_output=False,
            )
            replies = io.StringIO(f"{source}\n\n\n\n\n\n\n")

            with mock.patch("wisprsync.cli.commands.repo_root", return_value=root):
                with mock.patch("wisprsync.cli.commands.discover_sources", return_value=[]):
                    with mock.patch("sys.stdin", replies):
                        with mock.patch.object(replies, "isatty", return_value=True):
                            command_setup(args)

            config = json.loads((root / ".wisprsync" / "config.json").read_text(encoding="utf-8"))
            self.assertEqual(Path(config["source_database"]), source.resolve())

    def test_interactive_setup_prompts_for_output_and_displays_resolved_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            source = Path(tmp) / "app-data" / "flow.sqlite"
            root.mkdir()
            source.parent.mkdir()
            self._create_history_db(source)
            args = argparse.Namespace(
                source=str(source),
                output=None,
                schedule=False,
                yes=False,
                no_screenshots=False,
                allow_unsafe_output=False,
            )
            replies = io.StringIO("\nrelative-output\n\ny\n\n\n\n\n")
            output = io.StringIO()

            with mock.patch("wisprsync.cli.commands.repo_root", return_value=root):
                with mock.patch("sys.stdin", replies):
                    with mock.patch("sys.stdout", output):
                        with mock.patch.object(replies, "isatty", return_value=True):
                            command_setup(args)

            self.assertIn(f"Resolved output directory: {root / 'relative-output'}", output.getvalue())

    def test_interactive_setup_allows_repo_local_output_after_confirmation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            source = Path(tmp) / "app-data" / "flow.sqlite"
            root.mkdir()
            source.parent.mkdir()
            self._create_history_db(source)
            args = argparse.Namespace(
                source=str(source),
                output=None,
                schedule=False,
                yes=False,
                no_screenshots=False,
                allow_unsafe_output=False,
            )
            replies = io.StringIO("\ndata\n\ny\n\n\n\n\n")
            output = io.StringIO()

            with mock.patch("wisprsync.cli.commands.repo_root", return_value=root):
                with mock.patch("sys.stdin", replies):
                    with mock.patch("sys.stdout", output):
                        with mock.patch.object(replies, "isatty", return_value=True):
                            command_setup(args)

            self.assertIn("Warning: this output directory is inside the WisprSync repository.", output.getvalue())
            self.assertTrue((root / ".wisprsync" / "config.json").exists())

    def test_interactive_setup_aborts_without_writing_when_final_review_declined(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            source = Path(tmp) / "app-data" / "flow.sqlite"
            root.mkdir()
            source.parent.mkdir()
            self._create_history_db(source)
            args = argparse.Namespace(
                source=str(source),
                output=None,
                schedule=False,
                yes=False,
                no_screenshots=False,
                allow_unsafe_output=False,
            )
            replies = io.StringIO("\n\n\n\n\nn\n")

            with mock.patch("wisprsync.cli.commands.repo_root", return_value=root):
                with mock.patch("sys.stdin", replies):
                    with mock.patch.object(replies, "isatty", return_value=True):
                        self.assertEqual(command_setup(args), 1)

            self.assertFalse((root / ".wisprsync" / "config.json").exists())

    def test_interactive_setup_blocks_private_repo_state_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            source = Path(tmp) / "app-data" / "flow.sqlite"
            root.mkdir()
            source.parent.mkdir()
            self._create_history_db(source)
            args = argparse.Namespace(
                source=str(source),
                output=None,
                schedule=False,
                yes=False,
                no_screenshots=False,
                allow_unsafe_output=False,
            )

            for output_path in (".wisprsync/export", ".wisprsync-cache/export"):
                with self.subTest(output_path=output_path):
                    replies = io.StringIO(f"\n{output_path}\n")
                    with mock.patch("wisprsync.cli.commands.repo_root", return_value=root):
                        with mock.patch("sys.stdin", replies):
                            with mock.patch.object(replies, "isatty", return_value=True):
                                with self.assertRaises(WisprSyncError):
                                    command_setup(args)

            self.assertFalse((root / ".wisprsync" / "config.json").exists())

    def test_interactive_setup_existing_file_output_remains_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            source = Path(tmp) / "app-data" / "flow.sqlite"
            output = Path(tmp) / "export-file"
            root.mkdir()
            source.parent.mkdir()
            self._create_history_db(source)
            output.write_text("not a directory", encoding="utf-8")
            args = argparse.Namespace(
                source=str(source),
                output=None,
                schedule=False,
                yes=False,
                no_screenshots=False,
                allow_unsafe_output=False,
            )
            replies = io.StringIO(f"\n{output}\n")

            with mock.patch("wisprsync.cli.commands.repo_root", return_value=root):
                with mock.patch("sys.stdin", replies):
                    with mock.patch.object(replies, "isatty", return_value=True):
                        with self.assertRaises(WisprSyncError):
                            command_setup(args)

    def test_sync_runs_export_and_validate_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            output = Path(tmp) / "export"
            root.mkdir()
            (root / ".wisprsync").mkdir()
            (root / ".wisprsync" / "config.json").write_text(
                '{"output_directory": "%s"}\n' % output,
                encoding="utf-8",
            )
            args = argparse.Namespace(output=None, dry_run=False)

            with mock.patch("wisprsync.cli.commands.repo_root", return_value=root):
                with mock.patch("wisprsync.cli.commands.command_export", return_value=0):
                    with mock.patch("wisprsync.cli.commands.command_validate", return_value=0):
                        self.assertEqual(command_sync(args), 0)

    def test_cli_parser_rejects_git_sync_command(self) -> None:
        parser = build_parser()

        with self.assertRaises(SystemExit):
            parser.parse_args(["git-sync"])

    def test_sync_retains_records_missing_from_source_in_history_index(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            source = Path(tmp) / "app-data" / "flow.sqlite"
            output = Path(tmp) / "wispr_sync"
            root.mkdir()
            source.parent.mkdir()
            self._create_full_history_db(source, ["one", "two"])
            args = argparse.Namespace(
                source=str(source),
                output=str(output),
                include_screenshots=False,
                no_screenshots=False,
                dry_run=False,
                limit=None,
                allow_unsafe_output=False,
            )

            with mock.patch("wisprsync.export.runner.repo_root", return_value=root):
                with mock.patch("wisprsync.validate.runner.repo_root", return_value=root):
                    self.assertEqual(command_sync(args), 0)

            self._create_full_history_db(source, ["one"])
            with mock.patch("wisprsync.export.runner.repo_root", return_value=root):
                with mock.patch("wisprsync.validate.runner.repo_root", return_value=root):
                    self.assertEqual(command_sync(args), 0)

            rows = [
                json.loads(line)
                for line in (output / "indexes" / "history.jsonl").read_text(encoding="utf-8").splitlines()
            ]
            by_id = {row["id"]: row for row in rows}
            manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))

            self.assertEqual(by_id["one"]["source_status"], "current")
            self.assertEqual(by_id["two"]["source_status"], "missing_from_source")
            self.assertTrue((output / by_id["two"]["metadata_path"]).exists())
            self.assertEqual(manifest["counts"]["active_records"], 1)
            self.assertEqual(manifest["counts"]["retained_missing_from_source_records"], 1)
            self.assertEqual(manifest["counts"]["total_records"], 2)

    def test_successful_sync_prunes_source_backups_to_latest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            source = Path(tmp) / "app-data" / "flow.sqlite"
            output = Path(tmp) / "wispr_sync"
            backup_dir = root / ".wisprsync-cache" / "source-backups"
            root.mkdir()
            source.parent.mkdir()
            self._create_full_history_db(source, ["one"])
            args = argparse.Namespace(
                source=str(source),
                output=str(output),
                include_screenshots=False,
                no_screenshots=False,
                dry_run=False,
                limit=None,
                allow_unsafe_output=False,
            )

            times = [
                datetime(2026, 5, 10, tzinfo=timezone.utc),
                datetime(2026, 5, 10, 0, 0, 1, tzinfo=timezone.utc),
                datetime(2026, 5, 11, tzinfo=timezone.utc),
                datetime(2026, 5, 11, 0, 0, 1, tzinfo=timezone.utc),
            ]

            with mock.patch("wisprsync.export.runner.repo_root", return_value=root):
                with mock.patch("wisprsync.validate.runner.repo_root", return_value=root):
                    with mock.patch("wisprsync.export.runner.utc_now", side_effect=times):
                        self.assertEqual(command_sync(args), 0)
                        (backup_dir / "20260510T000000.000Z.sqlite-wal").write_text("", encoding="utf-8")
                        (backup_dir / "20260510T000000.000Z.sqlite-shm").write_text("", encoding="utf-8")
                        self.assertEqual(command_sync(args), 0)

            backup_files = sorted(path.name for path in backup_dir.iterdir())
            sqlite_backups = [name for name in backup_files if name.endswith(".sqlite")]
            self.assertEqual(sqlite_backups, ["20260511T000000.000Z.sqlite"])
            self.assertFalse(any(name.startswith("20260510T000000.000Z") for name in backup_files))

    def test_launch_agent_renders_midnight_repo_local_sync(self) -> None:
        root = Path("/tmp/WisprSync")

        rendered = render_launch_agent(root)

        self.assertIn(LABEL, rendered)
        self.assertIn(str(runner_executable_path(root)), rendered)
        self.assertIn("<key>Hour</key>", rendered)
        self.assertIn("<integer>0</integer>", rendered)

    def test_cleanup_repo_data_removes_only_repo_data(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            data = root / "data"
            data.mkdir(parents=True)
            (data / "manifest.json").write_text("{}", encoding="utf-8")
            args = argparse.Namespace(yes=True)

            with mock.patch("wisprsync.cli.commands.repo_root", return_value=root):
                self.assertEqual(command_cleanup_repo_data(args), 0)

            self.assertFalse(data.exists())

    @staticmethod
    def _create_history_db(path: Path) -> None:
        with sqlite3.connect(path) as conn:
            conn.execute('create table "History" (transcriptEntityId text)')

    @staticmethod
    def _create_full_history_db(path: Path, ids: list[str]) -> None:
        if path.exists():
            path.unlink()
        columns = ", ".join(f'"{column}" text' for column in HISTORY_COLUMNS)
        placeholders = ", ".join("?" for _ in HISTORY_COLUMNS)
        quoted = ", ".join(f'"{column}"' for column in HISTORY_COLUMNS)
        with sqlite3.connect(path) as conn:
            conn.execute(f'create table "History" ({columns})')
            conn.execute(
                'create table "Dictionary" (id text, phrase text, replacement text, teamDictionaryId text, '
                'lastUsed text, frequencyUsed text, remoteFrequencyUsed text, manualEntry text, createdAt text, '
                'modifiedAt text, isDeleted text, source text, isSnippet text, observedSource text, isStarred text)'
            )
            for index, record_id in enumerate(ids, start=1):
                values = {column: None for column in HISTORY_COLUMNS}
                values.update(
                    {
                        "transcriptEntityId": record_id,
                        "timestamp": f"2026-05-10T00:00:0{index}Z",
                        "asrText": f"raw {record_id}",
                        "formattedText": f"formatted {record_id}",
                        "status": "done",
                    }
                )
                conn.execute(
                    f'insert into "History" ({quoted}) values ({placeholders})',
                    [values[column] for column in HISTORY_COLUMNS],
                )


if __name__ == "__main__":
    unittest.main()

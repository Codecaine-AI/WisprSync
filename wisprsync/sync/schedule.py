from __future__ import annotations

import subprocess
from pathlib import Path

from wisprsync.core.errors import WisprSyncError

LABEL = "com.codecaine.wispr_sync_runner"
LEGACY_LABELS = ("com.codecaine.wisprsync",)


def launch_agent_path(label: str = LABEL) -> Path:
    return Path.home() / "Library" / "LaunchAgents" / f"{label}.plist"


def render_launch_agent(root: Path) -> str:
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>{LABEL}</string>
  <key>ProgramArguments</key>
  <array>
    <string>{root / "bin" / "wispr_sync_runner"}</string>
  </array>
  <key>WorkingDirectory</key>
  <string>{root}</string>
  <key>StartCalendarInterval</key>
  <dict>
    <key>Hour</key>
    <integer>0</integer>
    <key>Minute</key>
    <integer>0</integer>
  </dict>
  <key>StandardOutPath</key>
  <string>{root / ".wisprsync" / "schedule.out.log"}</string>
  <key>StandardErrorPath</key>
  <string>{root / ".wisprsync" / "schedule.err.log"}</string>
</dict>
</plist>
"""


def install_launch_agent(root: Path) -> Path:
    path = launch_agent_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    for legacy_label in LEGACY_LABELS:
        legacy_path = launch_agent_path(legacy_label)
        if legacy_path.exists():
            run_launchctl("unload", str(legacy_path), allow_failure=True)
            legacy_path.unlink()
    path.write_text(render_launch_agent(root), encoding="utf-8")
    run_launchctl("unload", str(path), allow_failure=True)
    run_launchctl("load", str(path))
    return path


def remove_launch_agent() -> Path:
    path = launch_agent_path()
    if path.exists():
        run_launchctl("unload", str(path), allow_failure=True)
        path.unlink()
    return path


def launch_agent_status() -> tuple[Path, bool]:
    path = launch_agent_path()
    return path, path.exists()


def run_launchctl(*args: str, allow_failure: bool = False) -> None:
    result = subprocess.run(["launchctl", *args], text=True, capture_output=True, check=False)
    if result.returncode != 0 and not allow_failure:
        detail = result.stderr.strip() or result.stdout.strip()
        raise WisprSyncError(f"launchctl {' '.join(args)} failed: {detail}")

from __future__ import annotations

import shutil
from pathlib import Path

from wisprsync.core.errors import WisprSyncError
from wisprsync.core.safety import is_same_or_child


def cleanup_repo_data(root: Path) -> bool:
    data_dir = root / "data"
    if not data_dir.exists():
        return False
    if not data_dir.is_dir():
        raise WisprSyncError(f"repo data path is not a directory: {data_dir}")
    if not is_same_or_child(data_dir, root) or data_dir.resolve() == root.resolve():
        raise WisprSyncError(f"refusing to clean unexpected data path: {data_dir}")
    shutil.rmtree(data_dir)
    return True

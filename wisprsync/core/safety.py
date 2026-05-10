from __future__ import annotations

from pathlib import Path

from wisprsync.core.errors import WisprSyncError


def resolved(path: Path | str) -> Path:
    return Path(path).expanduser().resolve()


def is_same_or_child(path: Path, parent: Path) -> bool:
    candidate = resolved(path)
    base = resolved(parent)
    return candidate == base or base in candidate.parents


def ensure_child(parent: Path, child: Path, label: str) -> None:
    if not is_same_or_child(child, parent):
        raise WisprSyncError(f"{label} is outside expected directory: {child}")


def known_wispr_app_roots() -> list[Path]:
    home = Path.home()
    return [
        home / "Library/Application Support/Wispr Flow",
        home / "Library/Application Support/Flow",
    ]


def unsafe_output_reasons(root: Path, source: Path, output: Path) -> list[str]:
    root_path = resolved(root)
    source_path = resolved(source)
    output_path = resolved(output)
    home_path = resolved(Path.home())
    reasons: list[str] = []

    if output.exists() and output.is_file():
        reasons.append("output path already exists as a file")

    if output_path == Path(output_path.anchor):
        reasons.append("output path is the filesystem root")
    if output_path == home_path:
        reasons.append("output path is the user home directory")
    if output_path == root_path:
        reasons.append("output path is the WisprSync repository root")

    for private_dir in (root_path / ".wisprsync", root_path / ".wisprsync-cache"):
        if output_path == private_dir or private_dir in output_path.parents:
            reasons.append(f"output path is inside private WisprSync state: {private_dir}")

    source_parent = source_path.parent
    if output_path == source_path:
        reasons.append("output path is the source database file")
    if output_path == source_parent or source_parent in output_path.parents:
        reasons.append("output path is inside the source database directory")
    if output_path in source_path.parents:
        reasons.append("output path is an ancestor of the source database")

    for app_root in known_wispr_app_roots():
        app_root_path = resolved(app_root)
        if output_path == app_root_path or app_root_path in output_path.parents:
            reasons.append(f"output path is inside Wispr Flow app data: {app_root_path}")

    return reasons


def validate_export_paths(root: Path, source: Path, output: Path, allow_unsafe_output: bool = False) -> None:
    reasons = unsafe_output_reasons(root, source, output)
    non_overridable = [reason for reason in reasons if reason == "output path already exists as a file"]
    if non_overridable:
        raise WisprSyncError("; ".join(non_overridable))
    if reasons and not allow_unsafe_output:
        raise WisprSyncError(
            "unsafe output path: "
            + "; ".join(reasons)
            + "; pass --allow-unsafe-output only if you intentionally want this location"
        )

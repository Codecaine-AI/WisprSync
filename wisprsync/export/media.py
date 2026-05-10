from __future__ import annotations

from typing import Any

from wisprsync.support.hashes import sha256_bytes


def media_info(blob: bytes | None, path: str, fmt: str | None) -> dict[str, Any]:
    if blob is None:
        return {"path": None, "present": False, "format": None, "size_bytes": None, "sha256": None}
    return {
        "path": path,
        "present": True,
        "format": fmt,
        "size_bytes": len(blob),
        "sha256": sha256_bytes(blob),
    }


def audio_format(blob: bytes | None) -> str | None:
    if blob and len(blob) >= 12 and blob[:4] == b"RIFF" and blob[8:12] == b"WAVE":
        return "wav_pcm_s16le_16000hz_mono"
    if blob:
        return "unknown"
    return None


def screenshot_format(blob: bytes | None) -> str | None:
    if blob and blob.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if blob:
        return "unknown"
    return None

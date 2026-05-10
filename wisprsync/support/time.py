from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso_z(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def compact_ts(dt: datetime | None) -> str:
    if dt is None:
        return "unknown-time"
    return dt.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%S") + f".{dt.microsecond // 1000:03d}Z"


def parse_timestamp(value: Any) -> datetime | None:
    if not value:
        return None
    text = str(value).strip()
    if not text:
        return None
    normalized = text.replace(" Z", "Z").replace(" +", "+").replace(" -", "-")
    candidates = [
        text,
        text.replace("Z", "+00:00"),
        normalized,
        normalized.replace("Z", "+00:00"),
        normalized.replace(" ", "T", 1),
    ]
    for candidate in candidates:
        try:
            dt = datetime.fromisoformat(candidate)
            if dt.tzinfo is None:
                return dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except ValueError:
            continue
    return None


def local_timestamp(timestamp_utc: datetime | None, offset_minutes: Any) -> str | None:
    if timestamp_utc is None:
        return None
    if offset_minutes is None:
        return iso_z(timestamp_utc)
    try:
        offset = int(offset_minutes)
    except (TypeError, ValueError):
        return iso_z(timestamp_utc)
    local_dt = timestamp_utc - timedelta(minutes=offset)
    tz = timezone(timedelta(minutes=-offset))
    return local_dt.replace(tzinfo=tz).isoformat(timespec="milliseconds")

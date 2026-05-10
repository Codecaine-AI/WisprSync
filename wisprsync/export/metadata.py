from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from wisprsync.core.constants import EXPORTER_VERSION, SCHEMA_VERSION
from wisprsync.core.paths import relative_to_output
from wisprsync.export.media import audio_format, media_info, screenshot_format
from wisprsync.support.hashes import sha256_bytes, sha256_json
from wisprsync.support.json import parse_json_field
from wisprsync.support.time import iso_z, local_timestamp, parse_timestamp


def bool_or_none(value: Any) -> bool | None:
    if value is None:
        return None
    return bool(value)


def build_metadata(
    row: dict[str, Any],
    source_database: Path,
    output: Path,
    record_dir: Path,
    exported_at: datetime,
    include_screenshots: bool,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    record_id = row["transcriptEntityId"]
    timestamp_utc = parse_timestamp(row.get("timestamp"))
    audio_blob = row.get("audio")
    screenshot_blob = row.get("screenshot") if include_screenshots else None

    raw_path = "raw_transcript.txt" if row.get("asrText") not in (None, "") else None
    formatted_path = "formatted_transcript.txt" if row.get("formattedText") not in (None, "") else None
    audio_path = "audio.wav" if audio_blob is not None else None
    screenshot_path = "screenshot.png" if screenshot_blob is not None else None

    audio = (
        media_info(audio_blob, audio_path or "audio.wav", audio_format(audio_blob))
        if audio_blob is not None
        else media_info(None, "audio.wav", None)
    )
    screenshot = (
        media_info(screenshot_blob, screenshot_path or "screenshot.png", screenshot_format(screenshot_blob))
        if screenshot_blob is not None
        else media_info(None, "screenshot.png", None)
    )

    source_hash_input = {
        "id": record_id,
        "timestamp": row.get("timestamp"),
        "status": row.get("status"),
        "text": {
            "asr": row.get("asrText"),
            "formatted": row.get("formattedText"),
            "edited": row.get("editedText"),
            "pasted": row.get("pastedText"),
            "default_asr": row.get("defaultAsrText"),
            "fallback_asr": row.get("fallbackAsrText"),
            "default_formatted": row.get("defaultFormattedText"),
            "fallback_formatted": row.get("fallbackFormattedText"),
        },
        "media": {
            "audio_sha256": audio["sha256"],
            "screenshot_sha256": screenshot["sha256"],
        },
        "context": {
            "app": row.get("app"),
            "url": row.get("url"),
            "additional_context": parse_json_field(row.get("additionalContext")),
            "textbox_contents": row.get("textboxContents"),
            "conversation_id": row.get("conversationId"),
            "mic_device": row.get("micDevice"),
            "language": row.get("language"),
            "detected_language": row.get("detectedLanguage"),
            "platform": row.get("platform"),
            "transcript_origin": row.get("transcriptOrigin"),
            "app_version": row.get("appVersion"),
            "timezone_offset_minutes": row.get("timezoneOffsetMinutes"),
        },
        "quality": {
            "e2e_latency": row.get("e2eLatency"),
            "client_network_latency": row.get("clientNetworkLatency"),
            "average_log_prob": row.get("averageLogProb"),
            "formatting_divergence_score": row.get("formattingDivergenceScore"),
            "fallback_asr_divergence_score": row.get("fallbackAsrDivergenceScore"),
            "fallback_formatting_divergence_score": row.get("fallbackFormattingDivergenceScore"),
            "used_fallback_asr": bool_or_none(row.get("usedFallbackAsr")),
            "used_fallback_formatting": bool_or_none(row.get("usedFallbackFormatting")),
            "called_external_asr": bool_or_none(row.get("calledExternalAsr")),
        },
        "edits": {
            "user_edit_metadata": parse_json_field(row.get("userEditMetaData")),
            "num_words_corrected": row.get("numWordsCorrected"),
            "num_dictionary_replacements": row.get("numDictionaryReplacements"),
            "has_reverted_ai": bool_or_none(row.get("hasRevertedAI")),
        },
    }
    source_row_sha256 = sha256_json(source_hash_input)

    metadata = {
        "schema_version": SCHEMA_VERSION,
        "id": record_id,
        "source": {
            "app": "Wispr Flow",
            "source_table": "History",
            "source_primary_key": "transcriptEntityId",
            "source_database_path": str(source_database),
        },
        "timestamps": {
            "timestamp_utc": iso_z(timestamp_utc) if timestamp_utc else None,
            "timestamp_local": local_timestamp(timestamp_utc, row.get("timezoneOffsetMinutes")),
            "timezone_offset_minutes": row.get("timezoneOffsetMinutes"),
            "exported_at_utc": iso_z(exported_at),
        },
        "status": {
            "wispr_status": row.get("status"),
            "edited_text_status": row.get("editedTextStatus"),
            "needs_uploading": bool_or_none(row.get("needsUploading")),
            "share_type": row.get("shareType"),
            "is_archived": bool_or_none(row.get("isArchived")),
        },
        "text": source_hash_input["text"],
        "text_stats": {
            "num_words": row.get("numWords"),
            "duration_seconds": row.get("duration"),
            "speech_duration_seconds": row.get("speechDuration"),
        },
        "media": {"audio": audio, "screenshot": screenshot},
        "context": source_hash_input["context"],
        "quality": source_hash_input["quality"],
        "edits": source_hash_input["edits"],
        "files": {
            "metadata": "metadata.json",
            "raw_transcript": raw_path,
            "formatted_transcript": formatted_path,
            "audio": audio_path,
            "screenshot": screenshot_path,
        },
        "integrity": {
            "source_row_sha256": source_row_sha256,
            "record_content_sha256": None,
            "exporter_version": EXPORTER_VERSION,
        },
    }

    content_hash_input = {
        "metadata": {**metadata, "integrity": {**metadata["integrity"], "record_content_sha256": None}},
        "files": {
            "raw_transcript_sha256": sha256_bytes(row["asrText"].encode("utf-8")) if raw_path else None,
            "formatted_transcript_sha256": sha256_bytes(row["formattedText"].encode("utf-8")) if formatted_path else None,
            "audio_sha256": audio["sha256"],
            "screenshot_sha256": screenshot["sha256"],
        },
    }
    metadata["integrity"]["record_content_sha256"] = sha256_json(content_hash_input)

    paths = {
        "metadata_path": relative_to_output(record_dir / "metadata.json", output),
        "raw_transcript_path": relative_to_output(record_dir / raw_path, output) if raw_path else None,
        "formatted_transcript_path": relative_to_output(record_dir / formatted_path, output) if formatted_path else None,
        "audio_path": relative_to_output(record_dir / audio_path, output) if audio_path else None,
        "screenshot_path": relative_to_output(record_dir / screenshot_path, output) if screenshot_path else None,
    }
    blobs = {"audio": audio_blob, "screenshot": screenshot_blob}
    return metadata, paths, blobs

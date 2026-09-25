from __future__ import annotations

import hashlib
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Mapping

from .v0101 import Document, SPEC_VERSION

ARTIFACT_EXTENSION = "starintel.artifact.v1"
WIRELESS_SECURITY_VALUES = frozenset(
    {
        "open",
        "wep",
        "wpa-psk",
        "wpa2-psk",
        "wpa2-enterprise",
        "wpa3-psk",
        "wpa3-enterprise",
        "wpa2wpa3-psk",
        "unknown",
    }
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def stable_artifact_id(dtype: str, dataset: str, content_hash: str, role: str = "") -> str:
    raw = f"{dtype}\x1f{dataset}\x1f{content_hash}\x1f{role}".encode("utf-8")
    return f"starintel:{dtype}:{hashlib.sha256(raw).hexdigest()}"


def build_file_document(
    *,
    dataset: str,
    uri: str,
    content_hash: str,
    size_bytes: int,
    original_name: str = "",
    declared_media_type: str = "application/octet-stream",
    sniffed_media_type: str = "application/octet-stream",
    magic_type: str = "",
    storage_id: str = "",
    kind: str = "file",
    quarantined: bool = True,
    executable: bool = False,
    parse_status: str = "unparsed",
    captured_at: str | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a content-addressed arbitrary-file record.

    File extensions are descriptive only. Security decisions are expected to
    use content hash, sniffed media type/magic, quarantine state, parser policy,
    and explicit capabilities.
    """

    if not dataset or not uri or not content_hash:
        raise ValueError("dataset, uri, and content_hash are required")
    if size_bytes < 0:
        raise ValueError("size_bytes must be non-negative")
    timestamp = captured_at or utc_now()
    data = {
        "name": original_name,
        "original_name": original_name,
        "uri": uri,
        "media_type": sniffed_media_type or declared_media_type,
        "size_bytes": size_bytes,
        "content_hash": content_hash,
        "hash_algorithm": "sha256",
        "storage_id": storage_id,
        "magic_type": magic_type,
        "hashes": {"sha256": content_hash.removeprefix("sha256:")},
        "quarantined": quarantined,
        "created_at": timestamp,
    }
    extension = {
        "kind": kind,
        "declared_media_type": declared_media_type,
        "sniffed_media_type": sniffed_media_type,
        "magic_type": magic_type,
        "quarantined": quarantined,
        "executable": executable,
        "parse_status": parse_status,
        "trust_filename_extension": False,
        "metadata": deepcopy(dict(metadata or {})),
    }
    document = {
        "_id": stable_artifact_id("file", dataset, content_hash, kind),
        "dataset": dataset,
        "dtype": "file",
        "schema_version": SPEC_VERSION,
        "version": 1,
        "date_added": timestamp,
        "date_updated": timestamp,
        "sources": [],
        "evidence": [],
        "data": data,
        "extensions": {ARTIFACT_EXTENSION: extension},
    }
    return Document.from_dict(document).to_dict()


def build_image_document(**kwargs: Any) -> dict[str, Any]:
    kwargs.setdefault("kind", "image")
    kwargs.setdefault("declared_media_type", "application/octet-stream")
    kwargs.setdefault("sniffed_media_type", "application/octet-stream")
    return build_file_document(**kwargs)


def build_video_document(
    *,
    duration_seconds: float | None = None,
    width: int | None = None,
    height: int | None = None,
    frame_rate: float | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    metadata = dict(kwargs.pop("metadata", {}) or {})
    if duration_seconds is not None:
        metadata["duration_seconds"] = duration_seconds
    if width is not None:
        metadata["width"] = width
    if height is not None:
        metadata["height"] = height
    if frame_rate is not None:
        metadata["frame_rate"] = frame_rate
    kwargs["metadata"] = metadata
    kwargs.setdefault("kind", "video")
    return build_file_document(**kwargs)


def build_video_frame_document(
    *,
    parent_file_id: str,
    frame_index: int,
    timestamp_ms: int,
    width: int,
    height: int,
    **kwargs: Any,
) -> dict[str, Any]:
    if frame_index < 0 or timestamp_ms < 0:
        raise ValueError("frame_index and timestamp_ms must be non-negative")
    metadata = dict(kwargs.pop("metadata", {}) or {})
    metadata.update(
        {
            "parent_file_id": parent_file_id,
            "frame_index": frame_index,
            "timestamp_ms": timestamp_ms,
            "width": width,
            "height": height,
        }
    )
    document = build_file_document(kind="video-frame", metadata=metadata, **kwargs)
    document["data"]["parent_file_id"] = parent_file_id
    document["data"]["extracted_metadata"] = {
        "frame_index": frame_index,
        "timestamp_ms": timestamp_ms,
        "width": width,
        "height": height,
    }
    return Document.from_dict(document).to_dict()


def build_pcap_capture_document(
    *,
    dataset: str,
    capture_id: str,
    file_uri: str,
    file_sha256: str,
    format: str = "pcapng",
    file_size_bytes: int | None = None,
    packet_count: int | None = None,
    capture_start: str | None = None,
    capture_end: str | None = None,
    capture_software: str = "",
    sensor_ref: str = "",
) -> dict[str, Any]:
    if format not in {"pcap", "pcapng", "unknown"}:
        raise ValueError("format must be pcap, pcapng, or unknown")
    now = utc_now()
    data: dict[str, Any] = {
        "capture_id": capture_id,
        "file_uri": file_uri,
        "file_sha256": file_sha256,
        "format": format,
        "capture_software": capture_software,
        "sensor_ref": sensor_ref,
    }
    if file_size_bytes is not None:
        data["file_size_bytes"] = file_size_bytes
    if packet_count is not None:
        data["packet_count"] = packet_count
    if capture_start is not None:
        data["capture_start"] = capture_start
    if capture_end is not None:
        data["capture_end"] = capture_end
    return Document.from_dict(
        {
            "_id": stable_artifact_id("pcap-capture", dataset, file_sha256, capture_id),
            "dataset": dataset,
            "dtype": "pcap-capture",
            "schema_version": SPEC_VERSION,
            "version": 1,
            "date_added": now,
            "date_updated": now,
            "sources": [],
            "evidence": [],
            "data": data,
            "extensions": {},
        }
    ).to_dict()


def build_wireless_network_document(
    *,
    dataset: str,
    bssid: str,
    security: str,
    ssid: str = "",
    auth_mode: str = "",
    cipher_suite: str = "",
    channel: int | None = None,
    frequency_mhz: int | None = None,
    band: str = "unknown",
    source_network_id: str = "",
    vendor: str = "",
    observed_at: str | None = None,
) -> dict[str, Any]:
    if security not in WIRELESS_SECURITY_VALUES:
        raise ValueError(f"unsupported security value: {security}")
    now = observed_at or utc_now()
    data: dict[str, Any] = {
        "bssid": bssid,
        "security": security,
        "ssid": ssid,
        "auth_mode": auth_mode,
        "cipher_suite": cipher_suite,
        "band": band,
        "source_network_id": source_network_id,
        "vendor": vendor,
        "last_seen": now,
    }
    if channel is not None:
        data["channel"] = channel
    if frequency_mhz is not None:
        data["frequency_mhz"] = frequency_mhz
    identity = hashlib.sha256(f"{bssid.casefold()}\x1f{ssid}".encode("utf-8")).hexdigest()
    return Document.from_dict(
        {
            "_id": f"starintel:wireless-network:{identity}",
            "dataset": dataset,
            "dtype": "wireless-network",
            "schema_version": SPEC_VERSION,
            "version": 1,
            "date_added": now,
            "date_updated": now,
            "sources": [],
            "evidence": [],
            "data": data,
            "extensions": {},
        }
    ).to_dict()

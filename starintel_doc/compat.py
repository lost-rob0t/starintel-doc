from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any

from .v0101 import (
    ACCEPTED_SPEC_VERSIONS,
    SPEC_VERSION,
    ValidationError,
    dtype_schemas,
    load_schema,
    roundtrip_document,
)

LEGACY_FLAT_VERSIONS = frozenset({"0.7.3", "0.8.0", "0.8.2"})
LEGACY_DTYPE_ALIASES = {
    "organization": "org",
    "organisation": "org",
    "investigation_target": "investigation-target",
    "social_media_post": "social-media-post",
    "email_message": "email-message",
    "financial_observation": "financial-observation",
    "research_pass": "research-pass",
    "dataset_manifest": "dataset-manifest",
    "actor_manifest": "actor-manifest",
    "legal_case": "legal-case",
    "lobbying_filing": "lobbying-filing",
    "campaign_finance": "campaign-finance",
    "network_device": "network-device",
}
ENVELOPE_KEYS = {
    "_id", "_rev", "id", "dataset", "dtype", "schema_version", "version",
    "date_added", "date_updated", "dateAdded", "dateUpdated", "sources",
    "evidence", "data", "extensions", "title", "summary", "description",
    "status", "language", "tags", "labels", "aliases", "keywords",
    "identifiers", "temporal", "provenance", "assessment", "verification",
    "handling", "lineage", "quality", "workflow", "geospatial", "attachments",
    "related_ids", "notes",
}
CAMEL_KEYS = {
    "isReply": "is_reply",
    "messageId": "message_id",
    "replyTo": "reply_to",
    "replyCount": "reply_count",
    "repostCount": "repost_count",
    "likeCount": "like_count",
    "viewCount": "view_count",
    "phoneType": "phone_type",
    "recordType": "record_type",
    "resolvedAddresses": "resolved_addresses",
    "targetOptions": "target_options",
    "consumerPath": "consumer_path",
}


def _iso(value: Any) -> str:
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, timezone.utc).isoformat().replace("+00:00", "Z")
    text = str(value or "").strip()
    if not text:
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    if text.endswith("Z"):
        return text
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.isoformat().replace("+00:00", "Z")


def _json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _coerce(value: Any, schema: dict[str, Any]) -> Any:
    if not schema:
        return deepcopy(value)
    if "anyOf" in schema:
        for candidate in schema["anyOf"]:
            expected = candidate.get("type")
            if expected == "null" and value is None:
                return None
            if expected == "string" and isinstance(value, str):
                return _coerce(value, candidate)
            if expected == "object" and isinstance(value, dict):
                return _coerce(value, candidate)
            if expected == "array" and isinstance(value, list):
                return _coerce(value, candidate)
        return None
    expected = schema.get("type")
    if expected == "string":
        if schema.get("format") == "date-time":
            return _iso(value)
        return str(value) if value is not None else ""
    if expected == "integer":
        try:
            return int(value)
        except (TypeError, ValueError):
            return None
    if expected == "number":
        try:
            number = float(value)
        except (TypeError, ValueError):
            return None
        if "minimum" in schema:
            number = max(float(schema["minimum"]), number)
        if "maximum" in schema:
            number = min(float(schema["maximum"]), number)
        return number
    if expected == "boolean":
        if isinstance(value, str):
            return value.strip().lower() in {"1", "true", "yes", "on"}
        return bool(value)
    if expected == "array":
        values = value if isinstance(value, list) else [value]
        converted = [_coerce(item, schema.get("items", {})) for item in values]
        return [item for item in converted if item is not None]
    if expected == "object":
        if not isinstance(value, dict):
            return None
        props = schema.get("properties", {})
        additional = schema.get("additionalProperties", True)
        result: dict[str, Any] = {}
        for key, item in value.items():
            if key in props:
                converted = _coerce(item, props[key])
                if converted is not None:
                    result[key] = converted
            elif additional is True:
                result[key] = deepcopy(item)
            elif isinstance(additional, dict):
                converted = _coerce(item, additional)
                if converted is not None:
                    result[key] = converted
        return result
    return deepcopy(value)


def _legacy_version(record: dict[str, Any]) -> str:
    schema_version = record.get("schema_version")
    if schema_version:
        return str(schema_version)
    version = record.get("version")
    if isinstance(version, str):
        return version
    return "legacy"


def _candidate_dtype(record: dict[str, Any], schemas: dict[str, dict[str, Any]]) -> str:
    raw = str(record.get("dtype") or "document").strip().lower().replace("_", "-")
    raw = LEGACY_DTYPE_ALIASES.get(raw, raw)
    return raw if raw in schemas else "document"


def _candidate_data(
    record: dict[str, Any],
    dtype: str,
    schemas: dict[str, dict[str, Any]],
) -> tuple[dict[str, Any], bool]:
    schema = schemas[dtype]
    properties = schema.get("properties", {})
    raw_data = record.get("data") if isinstance(record.get("data"), dict) else {}
    data: dict[str, Any] = {}
    for name, field_schema in properties.items():
        candidates = [name]
        candidates.extend(key for key, mapped in CAMEL_KEYS.items() if mapped == name)
        value = None
        found = False
        for key in candidates:
            if key in raw_data:
                value = raw_data[key]
                found = True
                break
            if key in record:
                value = record[key]
                found = True
                break
        if not found:
            continue
        converted = _coerce(value, field_schema)
        if converted is not None:
            data[name] = converted
    required = set(schema.get("required", []))
    return data, required.issubset(data)


def migrate_compatible_document(
    record: dict[str, Any],
    *,
    original_uri: str = "",
    schema: dict[str, Any] | None = None,
    preserve_inline_max_bytes: int = 262_144,
) -> dict[str, Any]:
    """Accept old StarIntel shapes and return a canonical 0.10.1 envelope.

    0.9.0 and 0.10.1 envelopes are validated directly. Older flat records are
    best-effort mapped into their canonical dtype. If required dtype fields
    cannot be reconstructed safely, the record is preserved as dtype=document
    rather than rejected or guessed.

    The exact legacy JSON is retained inline only when bounded. Migration
    workers should also persist the original bytes in object storage and pass
    original_uri, making the migration lossless even for large records.
    """

    if not isinstance(record, dict):
        raise TypeError("StarIntel record must be a JSON object")

    if record.get("schema_version") in ACCEPTED_SPEC_VERSIONS:
        return roundtrip_document(deepcopy(record), schema)

    schema = schema or load_schema()
    schemas = dtype_schemas(schema)
    original_dtype = str(record.get("dtype") or "document")
    dtype = _candidate_dtype(record, schemas)
    data, complete = _candidate_data(record, dtype, schemas)
    if not complete:
        dtype = "document"
        data, _ = _candidate_data(record, dtype, schemas)

    raw = _json_bytes(record)
    raw_hash = hashlib.sha256(raw).hexdigest()
    doc_id = str(record.get("_id") or record.get("id") or f"legacy:{raw_hash[:32]}")
    dataset = str(record.get("dataset") or "star-intel")
    added = _iso(record.get("date_added") or record.get("dateAdded"))
    updated = _iso(record.get("date_updated") or record.get("dateUpdated") or added)

    legacy_payload: dict[str, Any] = {
        "original_schema_version": _legacy_version(record),
        "original_dtype": original_dtype,
        "raw_sha256": raw_hash,
        "raw_size_bytes": len(raw),
        "migration": "starintel_doc.compat.migrate_compatible_document",
    }
    if original_uri:
        legacy_payload["original_uri"] = original_uri
    if len(raw) <= preserve_inline_max_bytes:
        legacy_payload["raw"] = deepcopy(record)
    else:
        legacy_payload["raw_inline"] = False

    existing_extensions = record.get("extensions")
    extensions = deepcopy(existing_extensions) if isinstance(existing_extensions, dict) else {}
    extensions["starintel.backcompat.v1"] = legacy_payload

    result: dict[str, Any] = {
        "_id": doc_id,
        "dataset": dataset,
        "dtype": dtype,
        "schema_version": SPEC_VERSION,
        "version": 1 if not isinstance(record.get("version"), int) else max(1, record["version"]),
        "date_added": added,
        "date_updated": updated,
        "sources": [],
        "evidence": [],
        "data": data,
        "extensions": extensions,
        "provenance": {
            "original_id": doc_id,
            "original_schema_version": _legacy_version(record),
            "imported_from": original_uri,
            "transform": "starintel_doc.compat.migrate_compatible_document",
            "software_version": SPEC_VERSION,
        },
        "lineage": {
            "migration_from": _legacy_version(record),
            "migration_notes": [
                "Read through StarIntel backwards-compatibility migration; newly emitted envelope is 0.10.1."
            ],
        },
    }
    if isinstance(record.get("_rev"), str):
        result["_rev"] = record["_rev"]
    for key in ("title", "summary", "description", "status", "language"):
        if isinstance(record.get(key), str):
            result[key] = record[key]

    try:
        return roundtrip_document(result, schema)
    except ValidationError:
        # The compatibility contract favors preserving old data over guessing.
        # A generic document envelope has no dtype-specific required fields.
        result["dtype"] = "document"
        result["data"] = {}
        result["extensions"]["starintel.backcompat.v1"]["mapping_fallback"] = True
        return roundtrip_document(result, schema)

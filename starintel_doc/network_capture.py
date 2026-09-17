from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Mapping

from .v090 import Document, SPEC_VERSION, ValidationError, load_schema

RELEASE_VERSION = "0.9.2"
PROFILE_VERSION = RELEASE_VERSION
PROFILE_ID = "https://spec.starintel.actor/profile/network-capture-v0.9.2.json"
CAPTCHA_SOLVE_CAPABILITY = "captcha.solve"
NETWORK_CAPTURE_DTYPES = frozenset({"http-transaction", "web-capture"})
SENSITIVE_HEADERS = frozenset(
    {
        "authorization",
        "proxy-authorization",
        "cookie",
        "set-cookie",
        "x-api-key",
        "x-auth-token",
    }
)

STR = {"type": "string"}
INT = {"type": "integer"}
NUM = {"type": "number"}
BOOL = {"type": "boolean"}
DATE_TIME = {"type": "string", "format": "date-time"}
NULLABLE_DATE_TIME = {"anyOf": [DATE_TIME, {"type": "null"}]}
STRS = {"type": "array", "items": STR}
JSON_MAP = {"type": "object", "additionalProperties": True}

CAPTCHA_CONTEXT_FIELDS: dict[str, Any] = {
    "challenge_status": STR,
    "captcha_detection_id": STR,
    "captcha_capability": STR,
    "browser_session_ref": STR,
    "network_context_ref": STR,
    "proxy_actor_uri": STR,
}

HTTP_TRANSACTION_FIELDS: dict[str, Any] = {
    "transaction_id": STR,
    "request_id": STR,
    "connection_id": STR,
    "parent_transaction_id": STR,
    "method": STR,
    "url": STR,
    "scheme": STR,
    "host": STR,
    "port": INT,
    "path": STR,
    "query": STR,
    "http_version": STR,
    "request_headers": JSON_MAP,
    "request_body_size": INT,
    "request_body_hash": STR,
    "request_body_artifact_uri": STR,
    "response_status": INT,
    "response_reason": STR,
    "response_headers": JSON_MAP,
    "response_body_size": INT,
    "response_body_hash": STR,
    "response_body_artifact_uri": STR,
    "started_at": NULLABLE_DATE_TIME,
    "ended_at": NULLABLE_DATE_TIME,
    "duration_ms": NUM,
    "remote_ip": STR,
    "remote_port": INT,
    "tls_version": STR,
    "tls_cipher": STR,
    "tls_server_name": STR,
    "certificate_sha256": STR,
    "redirect_from_id": STR,
    "redirect_to_id": STR,
    "capture_actor_uri": STR,
    **CAPTCHA_CONTEXT_FIELDS,
    "redacted_headers": STRS,
    "body_capture_policy": STR,
    "request_truncated": BOOL,
    "response_truncated": BOOL,
}

WEB_CAPTURE_FIELDS: dict[str, Any] = {
    "capture_id": STR,
    "url": STR,
    "final_url": STR,
    "title": STR,
    "status_code": INT,
    "browser": STR,
    "browser_version": STR,
    "viewport_width": INT,
    "viewport_height": INT,
    "device_scale_factor": NUM,
    "screenshot_uri": STR,
    "screenshot_hash": STR,
    "screenshot_media_type": STR,
    "screenshot_size_bytes": INT,
    "dom_artifact_uri": STR,
    "dom_artifact_hash": STR,
    "dom_artifact_size_bytes": INT,
    "captured_at": NULLABLE_DATE_TIME,
    "http_transaction_ids": STRS,
    "capture_actor_uri": STR,
    **CAPTCHA_CONTEXT_FIELDS,
}


def _data_schema(properties: dict[str, Any], required: tuple[str, ...]) -> dict[str, Any]:
    return {
        "type": "object",
        "properties": deepcopy(properties),
        "required": list(required),
        "additionalProperties": False,
    }


def profile_schema(base_schema: dict[str, Any] | None = None) -> dict[str, Any]:
    schema = deepcopy(base_schema or load_schema())
    dtype_definition = schema.get("properties", {}).get("dtype")
    if not isinstance(dtype_definition, dict):
        raise TypeError("base StarIntel schema is missing $.properties.dtype")
    allowed = dtype_definition.get("enum")
    if not isinstance(allowed, list):
        raise TypeError("base StarIntel schema dtype is not an enum")
    dtype_definition["enum"] = sorted(set(allowed) | NETWORK_CAPTURE_DTYPES)
    schema["$id"] = PROFILE_ID
    schema["title"] = "StarIntel v0.9.0 + network-capture profile v0.9.2"
    branches = schema.setdefault("allOf", [])
    branches.extend(
        [
            {
                "if": {"properties": {"dtype": {"const": "http-transaction"}}},
                "then": {
                    "properties": {
                        "data": _data_schema(
                            HTTP_TRANSACTION_FIELDS,
                            ("transaction_id", "method", "url", "response_status"),
                        )
                    }
                },
            },
            {
                "if": {"properties": {"dtype": {"const": "web-capture"}}},
                "then": {
                    "properties": {
                        "data": _data_schema(
                            WEB_CAPTURE_FIELDS,
                            ("capture_id", "url", "screenshot_uri", "screenshot_hash"),
                        )
                    }
                },
            },
        ]
    )
    return schema


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def redact_headers(headers: Mapping[str, Any]) -> tuple[dict[str, Any], list[str]]:
    clean: dict[str, Any] = {}
    redacted: list[str] = []
    for key, value in headers.items():
        name = str(key)
        if name.casefold() in SENSITIVE_HEADERS:
            clean[name] = "[REDACTED]"
            redacted.append(name)
        else:
            clean[name] = deepcopy(value)
    return clean, sorted(redacted, key=str.casefold)


def stable_capture_id(dtype: str, dataset: str, identity: Mapping[str, Any]) -> str:
    payload = json.dumps(
        {"dataset": dataset, "dtype": dtype, **dict(identity)},
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return f"starintel:{dtype}:{hashlib.sha256(payload).hexdigest()}"


def _validate(document: dict[str, Any]) -> dict[str, Any]:
    dtype = document.get("dtype")
    if dtype not in NETWORK_CAPTURE_DTYPES:
        raise ValidationError(
            "unknown_object_type",
            f"$.dtype: network-capture profile cannot validate {dtype!r}",
        )
    return Document.from_dict(document, profile_schema()).to_dict()


def _apply_capture_context(data: dict[str, Any], fields: Mapping[str, Any] | None) -> None:
    if fields:
        data.update(deepcopy(dict(fields)))
    if data.get("challenge_status") not in (None, "", "none"):
        data.setdefault("captcha_capability", CAPTCHA_SOLVE_CAPABILITY)


def build_http_transaction(
    *,
    dataset: str,
    method: str,
    url: str,
    response_status: int,
    transaction_id: str | None = None,
    request_headers: Mapping[str, Any] | None = None,
    response_headers: Mapping[str, Any] | None = None,
    observed_at: str | None = None,
    fields: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    if not dataset or not method or not url:
        raise ValueError("dataset, method, and url are required")
    timestamp = observed_at or utc_now()
    request, request_redacted = redact_headers(request_headers or {})
    response, response_redacted = redact_headers(response_headers or {})
    txid = transaction_id or stable_capture_id(
        "http-transaction",
        dataset,
        {
            "method": method.upper(),
            "url": url,
            "response_status": response_status,
            "observed_at": timestamp,
        },
    )
    data: dict[str, Any] = {
        "transaction_id": txid,
        "method": method.upper(),
        "url": url,
        "request_headers": request,
        "response_status": response_status,
        "response_headers": response,
        "redacted_headers": sorted(set(request_redacted + response_redacted), key=str.casefold),
        "started_at": timestamp,
        "ended_at": timestamp,
        "challenge_status": "none",
        "body_capture_policy": "artifact-reference-only",
    }
    _apply_capture_context(data, fields)
    document = {
        "_id": stable_capture_id("http-transaction", dataset, {"transaction_id": txid}),
        "dataset": dataset,
        "dtype": "http-transaction",
        "schema_version": SPEC_VERSION,
        "version": 1,
        "date_added": timestamp,
        "date_updated": timestamp,
        "sources": [],
        "evidence": [],
        "data": data,
        "extensions": {"starintel.profile": {"release_version": RELEASE_VERSION}},
    }
    return _validate(document)


def build_web_capture(
    *,
    dataset: str,
    url: str,
    screenshot_uri: str,
    screenshot_hash: str,
    capture_id: str | None = None,
    captured_at: str | None = None,
    fields: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    if not dataset or not url or not screenshot_uri or not screenshot_hash:
        raise ValueError("dataset, url, screenshot_uri, and screenshot_hash are required")
    timestamp = captured_at or utc_now()
    cid = capture_id or stable_capture_id(
        "web-capture",
        dataset,
        {"url": url, "screenshot_hash": screenshot_hash, "captured_at": timestamp},
    )
    data: dict[str, Any] = {
        "capture_id": cid,
        "url": url,
        "screenshot_uri": screenshot_uri,
        "screenshot_hash": screenshot_hash,
        "screenshot_media_type": "image/png",
        "captured_at": timestamp,
        "http_transaction_ids": [],
        "challenge_status": "none",
    }
    _apply_capture_context(data, fields)
    document = {
        "_id": stable_capture_id("web-capture", dataset, {"capture_id": cid}),
        "dataset": dataset,
        "dtype": "web-capture",
        "schema_version": SPEC_VERSION,
        "version": 1,
        "date_added": timestamp,
        "date_updated": timestamp,
        "sources": [],
        "evidence": [],
        "data": data,
        "extensions": {"starintel.profile": {"release_version": RELEASE_VERSION}},
    }
    return _validate(document)


def to_jsonld(document: Mapping[str, Any]) -> dict[str, Any]:
    value = _validate(deepcopy(dict(document)))
    data = value["data"]
    if value["dtype"] == "http-transaction":
        return {
            "@context": "https://schema.org",
            "@id": value["_id"],
            "@type": "Action",
            "name": f"HTTP {data['method']} transaction",
            "target": data["url"],
            "startTime": data.get("started_at"),
            "endTime": data.get("ended_at"),
            "result": {"@type": "Thing", "identifier": str(data["response_status"])},
        }
    return {
        "@context": "https://schema.org",
        "@id": value["_id"],
        "@type": "DigitalDocument",
        "url": data["url"],
        "encoding": {
            "@type": "MediaObject",
            "contentUrl": data["screenshot_uri"],
            "encodingFormat": data.get("screenshot_media_type", "image/png"),
            "sha256": data["screenshot_hash"],
        },
        "dateCreated": data.get("captured_at"),
    }

"""Canonical capture producers. Historical producers remain in network_capture."""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Mapping

from .canonical import SPEC_VERSION, validate_document
from .network_capture import (
    CAPTCHA_SOLVE_CAPABILITY, NETWORK_CAPTURE_DTYPES, redact_headers, stable_capture_id,
)


def _timestamp(value: str | None) -> tuple[str, int]:
    instant = datetime.fromisoformat(value.replace("Z", "+00:00")) if value else datetime.now(timezone.utc)
    if instant.tzinfo is None:
        raise ValueError("capture timestamps require a timezone")
    return instant.isoformat().replace("+00:00", "Z"), int(instant.timestamp())


def _finish(dtype: str, dataset: str, identifier: str, epoch: int,
            payload: dict, fields: Mapping[str, Any] | None) -> dict:
    # Python call arguments stay idiomatic snake_case; wire fields are canonical.
    # Schema validation below rejects undeclared keys, including legacy envelopes.
    if fields:
        payload.update(deepcopy(dict(fields)))
    if payload.get("challengeStatus") not in (None, "", "none"):
        payload.setdefault("captchaCapability", CAPTCHA_SOLVE_CAPABILITY)
    redacted = list(payload.get("redactedHeaders", []))
    for key in ("requestHeaders", "responseHeaders"):
        if key in payload:
            payload[key], names = redact_headers(payload[key])
            redacted.extend(names)
    if dtype == "http-transaction":
        payload["redactedHeaders"] = sorted(set(redacted), key=str.casefold)
    for key in ("durationMs", "deviceScaleFactor"):
        if key in payload and isinstance(payload[key], Decimal):
            payload[key] = format(payload[key], "f")
    envelope = {"id": identifier, "dataset": dataset, "dtype": dtype,
                "schemaVersion": SPEC_VERSION, "createdAt": epoch, "updatedAt": epoch}
    if set(payload) & set(envelope):
        raise ValueError("capture fields cannot override envelope fields")
    value = {**envelope, **payload}
    return validate_document(value)


def build_http_transaction(*, dataset: str, method: str, url: str, response_status: int,
                           transaction_id: str | None = None,
                           request_headers: Mapping[str, Any] | None = None,
                           response_headers: Mapping[str, Any] | None = None,
                           observed_at: str | None = None,
                           fields: Mapping[str, Any] | None = None) -> dict:
    timestamp, epoch = _timestamp(observed_at)
    txid = transaction_id or stable_capture_id("http-transaction", dataset,
            {"method": method.upper(), "url": url, "response_status": response_status,
             "observed_at": timestamp})
    payload = {"transactionId": txid, "method": method.upper(), "url": url,
               "responseStatus": response_status, "requestHeaders": dict(request_headers or {}),
               "responseHeaders": dict(response_headers or {}), "startedAt": timestamp,
               "endedAt": timestamp, "challengeStatus": "none",
               "bodyCapturePolicy": "artifact-reference-only"}
    return _finish("http-transaction", dataset,
                   stable_capture_id("http-transaction", dataset, {"transaction_id": txid}),
                   epoch, payload, fields)


def build_web_capture(*, dataset: str, url: str, screenshot_uri: str, screenshot_hash: str,
                      capture_id: str | None = None, captured_at: str | None = None,
                      fields: Mapping[str, Any] | None = None) -> dict:
    timestamp, epoch = _timestamp(captured_at)
    cid = capture_id or stable_capture_id("web-capture", dataset,
            {"url": url, "screenshot_hash": screenshot_hash, "captured_at": timestamp})
    payload = {"captureId": cid, "url": url, "screenshotUri": screenshot_uri,
               "screenshotHash": screenshot_hash, "screenshotMediaType": "image/png",
               "capturedAt": timestamp, "httpTransactionIds": [], "challengeStatus": "none"}
    return _finish("web-capture", dataset,
                   stable_capture_id("web-capture", dataset, {"capture_id": cid}),
                   epoch, payload, fields)


def to_jsonld(document: Mapping[str, Any]) -> dict:
    value = validate_document(deepcopy(dict(document)))
    if value["dtype"] not in NETWORK_CAPTURE_DTYPES:
        raise ValueError("expected a network-capture document")
    if value["dtype"] == "http-transaction":
        return {"@context": "https://schema.org", "@id": value["id"], "@type": "Action",
                "name": f"HTTP {value['method']} transaction", "target": value["url"],
                "startTime": value.get("startedAt"), "endTime": value.get("endedAt"),
                "result": {"@type": "Thing", "identifier": str(value["responseStatus"])}}
    return {"@context": "https://schema.org", "@id": value["id"], "@type": "DigitalDocument",
            "url": value["url"], "dateCreated": value.get("capturedAt"),
            "encoding": {"@type": "MediaObject", "contentUrl": value["screenshotUri"],
                         "encodingFormat": value.get("screenshotMediaType", "image/png"),
                         "sha256": value["screenshotHash"]}}

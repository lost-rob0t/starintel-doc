from __future__ import annotations

import copy

import pytest

from starintel_doc import (
    PROFILE_VERSION,
    SPEC_VERSION,
    build_http_transaction,
    build_web_capture,
    network_capture_to_jsonld,
    profile_schema,
)
from starintel_doc.network_capture import CAPTCHA_SOLVE_CAPABILITY, redact_headers
from starintel_doc.v090 import Document, ValidationError

NOW = "2026-09-17T01:00:00Z"


def test_release_is_additive_to_v09_wire():
    assert SPEC_VERSION == "0.9.0"
    assert PROFILE_VERSION == "0.9.2"
    dtypes = profile_schema()["properties"]["dtype"]["enum"]
    assert "http-transaction" in dtypes
    assert "web-capture" in dtypes


def test_http_transaction_redacts_auth_and_cookies():
    doc = build_http_transaction(
        dataset="fixture",
        method="get",
        url="https://example.test/a",
        response_status=403,
        observed_at=NOW,
        request_headers={"Authorization": "Bearer no", "Accept": "text/html"},
        response_headers={"Set-Cookie": "sid=no", "Content-Type": "text/html"},
        fields={
            "request_body_artifact_uri": "artifact://request/1",
            "request_body_hash": "sha256:req",
            "response_body_artifact_uri": "artifact://response/1",
            "response_body_hash": "sha256:resp",
            "challenge_status": "observed",
            "captcha_detection_id": "captcha-detection:fixture-1",
            "browser_session_ref": "star-secret://webdriver/session/fixture-1",
            "network_context_ref": "star-secret://network/context/fixture-1",
            "proxy_actor_uri": "star://proxy.starintel.actor/actor/egress",
        },
    )
    assert doc["data"]["method"] == "GET"
    assert doc["data"]["request_headers"]["Authorization"] == "[REDACTED]"
    assert doc["data"]["response_headers"]["Set-Cookie"] == "[REDACTED]"
    assert doc["data"]["body_capture_policy"] == "artifact-reference-only"
    assert doc["data"]["captcha_capability"] == CAPTCHA_SOLVE_CAPABILITY
    assert doc["data"]["browser_session_ref"].startswith("star-secret://")
    assert doc["data"]["network_context_ref"].startswith("star-secret://")
    Document.from_dict(doc, profile_schema())


def test_web_capture_is_artifact_backed():
    doc = build_web_capture(
        dataset="fixture",
        url="https://example.test/",
        screenshot_uri="artifact://screenshots/a.png",
        screenshot_hash="sha256:a",
        captured_at=NOW,
        fields={
            "viewport_width": 1440,
            "viewport_height": 900,
            "challenge_status": "observed",
            "browser_session_ref": "star-secret://webdriver/session/fixture-2",
        },
    )
    assert doc["data"]["screenshot_uri"].startswith("artifact://")
    assert doc["data"]["captcha_capability"] == CAPTCHA_SOLVE_CAPABILITY
    assert network_capture_to_jsonld(doc)["@type"] == "DigitalDocument"


def test_profile_rejects_unknown_capture_fields():
    doc = build_http_transaction(
        dataset="fixture",
        method="GET",
        url="https://example.test/",
        response_status=204,
        observed_at=NOW,
    )
    bad = copy.deepcopy(doc)
    bad["data"]["secret"] = "no"
    with pytest.raises(ValidationError) as error:
        Document.from_dict(bad, profile_schema())
    assert error.value.category == "undeclared_field"


def test_sensitive_header_matching_is_case_insensitive():
    headers, redacted = redact_headers({"COOKIE": "secret", "x-test": "ok"})
    assert headers["COOKIE"] == "[REDACTED]"
    assert headers["x-test"] == "ok"
    assert redacted == ["COOKIE"]

from decimal import Decimal

import pytest
import starintel_doc as runtime
from starintel_doc import network_capture as legacy

NOW = "2026-10-03T12:00:00Z"


def transaction(**kwargs):
    return runtime.build_http_transaction(dataset="fixture", method="get", url="https://example.test/",
                                          response_status=200, observed_at=NOW, **kwargs)


def test_default_capture_producers_are_canonical():
    for value in [transaction(), runtime.build_web_capture(dataset="fixture", url="https://example.test/",
            screenshot_uri="artifact://screenshots/1", screenshot_hash="sha256:test", captured_at=NOW)]:
        assert value["schemaVersion"] == "0.10.1"
        assert not ({"data", "schema_version", "_id"} & value.keys())
        assert isinstance(value["createdAt"], int)
        assert runtime.Document.from_dict(value).to_dict() == value
        assert runtime.network_capture_to_jsonld(value)["@id"] == value["id"]


def test_fields_cannot_bypass_header_redaction_or_wire_validation():
    value = transaction(fields={"requestHeaders": {"Authorization": "secret", "Accept": "text/plain"},
                               "responseHeaders": {"Set-Cookie": "secret"},
                               "durationMs": Decimal("1.25"), "challengeStatus": "observed"})
    assert value["requestHeaders"]["Authorization"] == "[REDACTED]"
    assert value["responseHeaders"]["Set-Cookie"] == "[REDACTED]"
    assert value["durationMs"] == "1.25"
    assert value["captchaCapability"] == "captcha.solve"
    for fields in [{"schemaVersion": "0.9.0"}, {"id": "override"}, {"response_status": 201}, {"data": {}}]:
        with pytest.raises((ValueError, runtime.ValidationError)):
            transaction(fields=fields)


def test_historical_producer_remains_explicit():
    old = legacy.build_http_transaction(dataset="fixture", method="get", url="https://example.test/",
                                        response_status=200, observed_at=NOW)
    assert old["schema_version"] == "0.9.0"
    assert "data" in old

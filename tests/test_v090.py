from __future__ import annotations

import unittest

from starintel_doc.v090 import SPEC_VERSION, UnsupportedVersion, ValidationError, roundtrip_document, validate_document


def document() -> dict:
    return {
        "_id": "starintel:person:python-test",
        "dataset": "test",
        "dtype": "person",
        "schema_version": SPEC_VERSION,
        "version": 1,
        "date_added": "2026-01-02T03:04:05Z",
        "date_updated": "2026-01-02T03:04:05+00:00",
        "sources": [],
        "evidence": [],
        "data": {"fname": "Ada", "lname": "Lovelace", "bio": "Unicode λ 漢字 🧠"},
        "extensions": {
            "example.test": {
                "integer": 9007199254740991,
                "number": 1.25,
                "null": None,
                "empty_array": [],
                "empty_object": {},
            }
        },
    }


class V090Tests(unittest.TestCase):
    def test_roundtrip(self) -> None:
        value = document()
        self.assertEqual(value, roundtrip_document(value))

    def test_missing_required_field(self) -> None:
        value = document()
        del value["_id"]
        with self.assertRaises(ValidationError) as context:
            validate_document(value)
        self.assertEqual(context.exception.category, "missing_required_field")

    def test_unsupported_version(self) -> None:
        value = document()
        value["schema_version"] = "0.8.0"
        with self.assertRaises(UnsupportedVersion):
            validate_document(value)


if __name__ == "__main__":
    unittest.main()

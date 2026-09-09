from __future__ import annotations

import unittest

from starintel_doc.v090 import SPEC_VERSION, roundtrip_document, validate_document


def operation_document() -> dict:
    return {
        "_id": "starintel:operation:python-091",
        "dataset": "conformance-v0.9.1",
        "dtype": "operation",
        "schema_version": SPEC_VERSION,
        "version": 1,
        "date_added": "2026-09-09T01:00:00Z",
        "date_updated": "2026-09-09T01:00:00Z",
        "sources": [],
        "evidence": [],
        "data": {
            "mission": "Exercise operation support in the Python binding.",
            "status": "planned",
            "phases": [
                {
                    "phase_id": "plan",
                    "objective": "Prove native operation round-trip.",
                    "state": "planned",
                    "depends_on": [],
                    "dataset_binding_ids": [],
                    "required_capability_ids": [],
                }
            ],
        },
    }


class Operation091Tests(unittest.TestCase):
    def test_operation_validates_and_roundtrips(self) -> None:
        value = operation_document()
        self.assertIs(value, validate_document(value))
        self.assertEqual(value, roundtrip_document(value))


if __name__ == "__main__":
    unittest.main()

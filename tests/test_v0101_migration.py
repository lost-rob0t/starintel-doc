from __future__ import annotations

import unittest

from starintel_doc.migration import load_compatibility_fixtures, migrate_batch
from starintel_doc.v0101 import SPEC_VERSION, document_definitions, validate_document


class V0101MigrationTests(unittest.TestCase):
    def test_authority_documents_are_available(self) -> None:
        definitions = document_definitions()
        for dtype in (
            "file",
            "picture",
            "video",
            "audio",
            "transcript",
            "person-identifier",
            "geo-point",
            "location",
        ):
            self.assertIn(dtype, definitions)

    def test_shared_compatibility_fixtures(self) -> None:
        for case in load_compatibility_fixtures()["cases"]:
            with self.subTest(case=case["name"]):
                self.assertEqual(case["expected"], migrate_batch([case["input"]]))

    def test_migration_is_idempotent(self) -> None:
        fixture = load_compatibility_fixtures()["cases"][0]
        first = migrate_batch([fixture["input"]])
        second = migrate_batch(first["documents"])
        self.assertEqual(first, second)

    def test_canonical_validation_rejects_snake_case(self) -> None:
        document = {
            "id": "person-invalid",
            "dataset": "fixture",
            "dtype": "person",
            "schemaVersion": SPEC_VERSION,
            "first_name": "Ada",
        }
        with self.assertRaises(Exception):
            validate_document(document)

    def test_batch_quarantines_bad_document_and_continues(self) -> None:
        fixtures = load_compatibility_fixtures()["cases"]
        result = migrate_batch([fixtures[-1]["input"], fixtures[0]["input"]])
        self.assertEqual([{"reasonCode": "ambiguousFieldCollision"}], result["quarantine"])
        self.assertEqual("person-current", result["documents"][0]["id"])


if __name__ == "__main__":
    unittest.main()

import copy
import json
import subprocess
import sys
import unittest

import starintel_doc as runtime
from starintel_doc.canonical import DOCUMENT_TYPES, generated

SCHEMA = runtime.load_schema()


def sample(node):
    if "$ref" in node:
        return sample(SCHEMA["$defs"][node["$ref"].split("/")[-1]])
    if "enum" in node:
        return node["enum"][0]
    if "anyOf" in node:
        return sample(node["anyOf"][0])
    kind = node.get("type")
    if kind == "object":
        return {key: sample(node["properties"][key]) for key in node.get("required", [])}
    if kind == "array":
        return []
    if kind in ("integer", "number"):
        return node.get("minimum", 0)
    if kind == "boolean":
        return False
    if node.get("format") == "date-time":
        return "2026-10-03T12:00:00Z"
    if node.get("format") == "date":
        return "2026-10-03"
    if node.get("format") == "uri":
        return "https://example.test/"
    if "pattern" in node:
        if "@" in node["pattern"]:
            return "fixture@example.test"
        if "0-9()." in node["pattern"]:
            return "+123456789"
        return "0"
    return "fixture"


def document(dtype):
    value = sample(SCHEMA["$defs"][DOCUMENT_TYPES[dtype]])
    value.update(id="fixture:" + dtype, dataset="conformance", dtype=dtype, schemaVersion="0.10.1")
    if dtype == "operation":
        value["phases"] = [{"phaseId": "collect", "objective": "Collect", "state": "planned"}]
    return value


class CanonicalTests(unittest.TestCase):
    def test_generated_bindings_and_adapter_all_document_types(self):
        self.assertEqual(runtime.SPEC_VERSION, "0.10.1")
        self.assertTrue({"operation", "research-node", "event", "alert", "source", "claim"}.issubset(DOCUMENT_TYPES))
        for dtype, name in DOCUMENT_TYPES.items():
            with self.subTest(dtype=dtype):
                value = document(dtype)
                self.assertEqual(getattr(generated, name)(**value), value)
                self.assertEqual(runtime.Document.from_dict(value).to_dict(), value)
                response = subprocess.run([sys.executable, "-m", "starintel_doc.conformance_adapter"],
                                          input=json.dumps({"command": "roundtrip", "document": value}),
                                          text=True, capture_output=True)
                self.assertEqual(response.returncode, 0, response.stdout + response.stderr)
                self.assertEqual(json.loads(response.stdout)["document"], value)

    def test_rejects_incompatible_wire_and_referenced_constraints(self):
        cases = [("person", "id", "invalid space"), ("person", "createdAt", -1),
                 ("geo-point", "latitude", "90.00000001"), ("person", "confidence", "0.12345"),
                 ("person", "confidence", "1.1"), ("person", "confidence", 0.5),
                 ("person", "dob", "2026-02-30"), ("url", "url", "invalid URL with spaces"),
                 ("person", "dtype", "made-up"), ("person", "schemaVersion", "0.10.2"),
                 ("person", "data", {}), ("person", "_id", "legacy"),
                 ("person", "sources", [{"id": "source"}]), ("wireless-network", "security", "wpa4")]
        for dtype, key, invalid in cases:
            with self.subTest(dtype=dtype, key=key, invalid=invalid):
                value = document(dtype)
                value[key] = invalid
                with self.assertRaises(runtime.ValidationError):
                    runtime.validate_document(value)
        value = document("wireless-station")
        del value["mac"]
        with self.assertRaises(runtime.ValidationError):
            runtime.validate_document(value)

    def test_preserves_opaque_extensions_and_optional_omission(self):
        value = document("person")
        value.update(deleted=False, extensions={"example.vendor": {"opaque_key": None, "flag": False, "items": []}})
        original = copy.deepcopy(value)
        self.assertEqual(runtime.roundtrip_document(value), original)
        self.assertEqual(value, original)

    def test_fake_nested_0101_is_rejected(self):
        with self.assertRaises(runtime.UnsupportedVersion):
            runtime.validate_document({"_id": "old", "dtype": "person", "schema_version": "0.10.1", "data": {}})


class ResearchFixturesTests(unittest.TestCase):
    def test_locked_research_semantic_fixtures(self):
        from starintel_canonical import RELEASE_ROOT
        fixtures = json.loads((RELEASE_ROOT / "research-fixtures.json").read_text())
        for fixture in fixtures:
            with self.subTest(fixture=fixture["name"]):
                if fixture["valid"]:
                    self.assertEqual(runtime.roundtrip_document(fixture["document"]), fixture["document"])
                else:
                    with self.assertRaises(runtime.ValidationError):
                        runtime.validate_document(fixture["document"])

    def test_transient_helpers_are_not_corpus_dtypes(self):
        self.assertNotIn("operation-phase", DOCUMENT_TYPES)


class SupportedWorkflowFixturesTests(unittest.TestCase):
    def test_full_payload_fixtures_and_map_uniqueness(self):
        from starintel_canonical import RELEASE_ROOT
        fixtures = json.loads((RELEASE_ROOT / "supported-workflow-fixtures.json").read_text())
        for fixture in fixtures:
            with self.subTest(dtype=fixture["document"]["dtype"]):
                self.assertEqual(runtime.roundtrip_document(fixture["document"]), fixture["document"])
        manifest = copy.deepcopy(next(f["document"] for f in fixtures if f["document"]["dtype"] == "dataset-manifest"))
        manifest["countsByDtype"].append({"key": manifest["countsByDtype"][0]["key"], "value": 999})
        with self.assertRaises(runtime.ValidationError): runtime.validate_document(manifest)

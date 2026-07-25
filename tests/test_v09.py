from __future__ import annotations

import unittest

from starintel_doc.documents import STARINTEL_DOC_VERSION, Document
from starintel_doc.entities import Org, Person
from starintel_doc.relations import Relation
from starintel_doc.schema_org import CANONICAL_DTYPES, DTYPE_SCHEMA_ORG_TYPES
from starintel_doc.web import Domain, Email


class StarIntelV09Tests(unittest.TestCase):
    def test_base_document_uses_v09_envelope(self) -> None:
        document = Document(dataset="test", title="Example").to_dict()
        self.assertEqual(document["schema_version"], "0.9.0")
        self.assertEqual(document["version"], 1)
        self.assertIsInstance(document["date_added"], str)
        self.assertEqual(document["schema_org"]["@context"], "https://schema.org/")
        self.assertEqual(document["schema_org"]["@id"], document["_id"])
        self.assertEqual(STARINTEL_DOC_VERSION, "0.9.0")

    def test_legacy_org_constructor_serializes_fields_under_data(self) -> None:
        org = Org(dataset="test", name="Example Org", etype="company", country="US")
        document = org.to_dict()
        self.assertEqual(document["dtype"], "org")
        self.assertEqual(document["data"]["name"], "Example Org")
        self.assertEqual(document["data"]["etype"], "company")
        self.assertNotIn("name", {key for key in document if key != "data"})
        self.assertEqual(document["schema_org"]["@type"], "Organization")

    def test_person_and_relation_schema_org_types(self) -> None:
        person = Person(dataset="test", fname="Ada", lname="Lovelace", etype="person").to_dict()
        relation = Relation(
            dataset="test",
            source=person["_id"],
            target="starintel:org:example",
            predicate="worked_for",
        ).to_dict()
        self.assertEqual(person["schema_org"]["@type"], "Person")
        self.assertEqual(relation["schema_org"]["@type"], "Role")
        self.assertEqual(relation["data"]["predicate"], "worked_for")
        self.assertEqual(relation["data"]["subject"], person["_id"])
        self.assertEqual(relation["data"]["object"], "starintel:org:example")

    def test_domain_and_email_required_fields(self) -> None:
        domain = Domain(dataset="test", record_type="A", record="example.com").to_dict()
        email = Email(dataset="test", user="ada", domain="example.com").to_dict()
        self.assertEqual(domain["data"]["domain"], "example.com")
        self.assertEqual(email["data"]["address"], "ada@example.com")

    def test_schema_org_map_covers_v09_dtype_set(self) -> None:
        self.assertEqual(set(CANONICAL_DTYPES), set(DTYPE_SCHEMA_ORG_TYPES))


if __name__ == "__main__":
    unittest.main()

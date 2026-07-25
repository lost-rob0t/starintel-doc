# StarIntel Python v0.9

The Python package now preserves the existing subclass constructors while emitting the canonical StarIntel v0.9 wire envelope.

Subtype dataclass fields serialize under `data`. Common metadata remains top-level, including ISO-8601 timestamps, structured sources, evidence, provenance, handling, geospatial metadata, and the declared `schema_org` JSON-LD block.

```python
from starintel_doc.entities import Org

organization = Org(dataset="example", name="Example Org", etype="company")
wire = organization.to_dict()

assert wire["schema_version"] == "0.9.0"
assert wire["data"]["name"] == "Example Org"
assert wire["schema_org"]["@type"] == "Organization"
```

`to_schema_org()` returns the expanded Schema.org JSON-LD projection. Explicit values in `schema_org` override deterministic defaults.

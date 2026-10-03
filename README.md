# StarIntel documents for Python

StarLang is the only specification authority. This package defaults to its
immutable generated **0.10.1** release. The full release is packaged beneath
`starintel_canonical/_release`; `schema/starintel-schema.lock.json` pins its source
commit and every vendored file. Do not edit generated artifacts downstream.

```python
from starintel_doc import Document, validate_document
person = {"id": "person:ada", "dataset": "example", "dtype": "person",
          "schemaVersion": "0.10.1", "fname": "Ada"}
validate_document(person)
assert Document.from_dict(person).to_dict() == person
```

The runtime selects concrete document definitions from the generated manifest,
follows schema references, checks formats, and enforces exact decimal bounds
and scale from that manifest. Decimal wire values remain strings. Flat camelCase
fields are canonical; nested `data`, `_id`, and `schema_version` are rejected.

Historical formats remain explicitly available in `starintel_doc.v090` and the
legacy model modules. `starintel_doc.network_capture` retains its historical
0.9.2 builders; those builders do not emit the canonical 0.10.1 format. The
conformance adapter selects 0.9 only for an explicit `spec_version: "0.9.0"`.
No automatic relabeling or corpus migration is performed.

```sh
python3 scripts/sync-starintel-schema.py --commit FULL_IMMUTABLE_STARLANG_SHA --destination starintel_canonical/_release
python3 scripts/sync-starintel-schema.py       # exact upstream comparison (CI)
python3 scripts/sync-starintel-schema.py --offline  # complete local package closure
python3 -m pytest -q
python3 -m build
nix flake check -L
```

Canonical migration policy and fixtures are consumed from the packaged release.
Migration implementations must pass those fixtures before claiming support.

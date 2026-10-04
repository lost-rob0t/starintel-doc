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

### Exact JSON numbers

Use `parse_json` and `stringify_json` from `starintel_doc` or
`starintel_canonical` at wire boundaries, or use `Document.from_json()` and
`Document.to_json()`. Integers use Python `int`; fractional and exponent tokens
use `decimal.Decimal` or the `RawJsonNumber` fallback described below, so opaque
JSON values retain their exact numeric
value, including values outside IEEE-754 range. These helpers never convert an
exact number through `float`. Decimal/exponent spellings may be normalized, but
coefficients and values are not rounded. Integral decimal/exponent tokens satisfy
JSON Schema `integer`; nonintegral tokens do not. Schema-declared decimal fields
continue to use strings, with the same generated bounds and scale validation.

`roundtrip_document` and `Document.to_dict()` also return these exact number
representations for fractional/exponent tokens. Serialize those dictionaries with
`stringify_json`, since stdlib `json.dumps` does not support these representations. Previously
rounded input from `json.loads` cannot be repaired: use the SDK parser on the
original JSON text. Non-finite numbers, non-string map keys, cyclic containers,
and non-JSON host values remain rejected.

Tokens beyond Decimal's exponent range use the SDK's `RawJsonNumber` fallback,
which preserves the original validated lexeme and compares values through sign,
coefficient digits, and decimal order. It never expands an exponent-sized power.
Both representations enforce the same generated numeric bounds and mathematical
integer semantics. `RawJsonNumber` supports exact comparison and serialization,
not arithmetic. Integers do not inherit CPython's normal string-digit conversion
limit. Applications may impose bounded input sizes at their own transport layer;
this does not narrow the unchanged StarLang authority.

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

### Capture producers

The package-root `build_http_transaction` and `build_web_capture` functions emit
canonical flat 0.10.1 documents validated against the pinned generated release.
Python keyword arguments stay snake_case; the optional `fields` mapping uses
canonical lowerCamelCase keys. Decimal wire values must be decimal strings (or
`Decimal` for `durationMs` / `deviceScaleFactor`). Envelope fields cannot be
replaced through `fields`. Headers are redacted after field overrides.

Historical 0.9.2 capture behavior remains explicitly available from
`starintel_doc.network_capture`; its `profile_schema` is also available as
`starintel_doc.legacy_profile_schema`. Existing historical documents are not
rewritten or silently relabeled.

Research operation and investigation-target contracts are pinned from StarLang #197.
Only persistent document types are exposed. Operation DAG, local reference, scope
and completion evidence rules run after structural validation using the locked
upstream reference implementation. Historical records remain unchanged.

The pending supported-workflow closure additionally pins published StarLang 9198370.
Inventory is manifest-derived. All28 added legacy domain types have dual-oracle
fixtures, explicit field mappings and preservation tests. Dataset-manifest typed
count entries enforce unique original map keys. This is runtime support, not a
claim that every producer or historical corpus has been migrated.


Explicit historical migration is available as
`starintel_canonical.migration.canonicalize_document(document, dtype_registry=...)`.
It does not run implicitly on current-wire validation. It preserves the original
nested payload and envelope metadata under `extensions.legacy.original`, including
source/evidence/handling details, and retains existing opaque extensions. It
requires explicit known types for references and rejects normalized collisions.
It does not infer types from ID prefixes or create related entities. Decimal
values are serialized without exponents. Timestamp fractions/offsets remain in
the original record even when envelope Unix metadata is emitted.

This helper is not proof of complete semantic migration for shared-name legacy
types: incompatible private payload fields (such as person external-ID arrays)
need source-backed mappings and may reject until those mappings are established.
Consumers must preserve the explicit legacy boundary while that work remains.

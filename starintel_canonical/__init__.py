"""Runtime consumer of StarLang's immutable generated StarIntel release."""
from __future__ import annotations

import json
import math
from copy import deepcopy
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker, validators

from ._release.generated import starintel_types as generated
from .errors import ValidationError, UnsupportedVersion
from .numbers import RawJsonNumber, parse_fraction
from ._release.operation_semantics import validate_operation_semantics
from ._release.workflow_semantics import validate_workflow_semantics
from jsonschema.exceptions import ValidationError as JsonSchemaValidationError

def category_for(error: JsonSchemaValidationError) -> str:
    if error.validator == "required":
        return "missing_required_field"
    if error.validator == "additionalProperties":
        return "undeclared_field"
    if error.validator == "format":
        return "invalid_datetime"
    if error.validator == "minimum":
        return "below_minimum"
    if error.validator == "maximum":
        return "above_maximum"
    if error.validator == "pattern":
        return "pattern_mismatch"
    if error.validator == "enum":
        return "invalid_enum"
    if error.validator == "const":
        return "unsupported_spec_version" if list(error.absolute_path) == ["schema_version"] else "invalid_constant"
    if error.validator in {"type", "anyOf"}:
        return "wrong_type"
    return "validation_error"


SPEC_VERSION = "0.10.1"
ADAPTER_VERSION = 1
RELEASE_ROOT = Path(__file__).parent / "_release"
MANIFEST = json.loads((RELEASE_ROOT / "generated/portable-manifest.json").read_text())
FORMAT_CHECKER = FormatChecker()


def _is_integer(checker: Any, value: Any) -> bool:
    # JSON Schema integer includes mathematically integral decimal/exponent
    # tokens. Never coerce a fractional token through binary floating point.
    if isinstance(value, RawJsonNumber):
        return value.is_integer()
    if isinstance(value, Decimal):
        return value.is_finite() and value == value.to_integral_value()
    return Draft202012Validator.TYPE_CHECKER.is_type(value, "integer")


def _is_number(checker: Any, value: Any) -> bool:
    return isinstance(value, RawJsonNumber) or Draft202012Validator.TYPE_CHECKER.is_type(value, "number")


_EXACT_VALIDATOR = validators.extend(
    Draft202012Validator,
    type_checker=Draft202012Validator.TYPE_CHECKER.redefine_many({"integer": _is_integer, "number": _is_number}),
)


def definition_name(name: str) -> str:
    return "".join(part.capitalize() for part in name.rsplit("/", 1)[-1].split("-"))


DOCUMENT_TYPES = {
    entry["name"].rsplit("/", 1)[-1]: definition_name(entry["name"])
    for entry in MANIFEST["types"] if entry["kind"] == "document" and entry["persistence"] == "persistent"
}
DECIMALS = {
    definition_name(entry["name"]): entry
    for entry in MANIFEST["types"]
    if entry["kind"] == "scalar" and entry["base"] == "decimal"
}


def load_schema() -> dict[str, Any]:
    return json.loads((RELEASE_ROOT / "generated/schema.json").read_text())


def decimal_constraints(value: Any, node: dict, schema: dict, path: str = "$") -> None:
    """Enforce decimal bounds/scale carried by the manifest, using exact values."""
    if "$ref" in node:
        name = node["$ref"].rsplit("/", 1)[-1]
        constraint = DECIMALS.get(name)
        if constraint is not None and isinstance(value, str):
            number = Decimal(value)
            if "minimum" in constraint and number < Decimal(str(constraint["minimum"])):
                raise ValidationError("below_minimum", f"{path}: below decimal minimum")
            if "maximum" in constraint and number > Decimal(str(constraint["maximum"])):
                raise ValidationError("above_maximum", f"{path}: above decimal maximum")
            if "scale" in constraint and len(value.partition(".")[2]) > constraint["scale"]:
                raise ValidationError("invalid_scale", f"{path}: exceeds decimal scale")
        decimal_constraints(value, schema["$defs"][name], schema, path)
    elif "anyOf" in node:
        for branch in node["anyOf"]:
            candidate = {**schema, "$ref": None}
            candidate.pop("$ref", None)
            candidate.update(branch)
            if _EXACT_VALIDATOR(candidate, format_checker=FORMAT_CHECKER).is_valid(value):
                decimal_constraints(value, branch, schema, path)
                break
    elif isinstance(value, dict):
        for name, item in value.items():
            child = node.get("properties", {}).get(name, node.get("additionalProperties", {}))
            if isinstance(child, dict):
                decimal_constraints(item, child, schema, f"{path}.{name}")
    elif isinstance(value, list) and isinstance(node.get("items"), dict):
        for index, item in enumerate(value):
            decimal_constraints(item, node["items"], schema, f"{path}[{index}]")


def validate_json_value(value: Any, path: str = "$", ancestors: set[int] | None = None) -> None:
    """Opaque extensions are JSON values, never arbitrary/non-finite host objects."""
    if value is None or isinstance(value, (str, bool, int, RawJsonNumber)):
        return
    if isinstance(value, (float, Decimal)):
        if not (value.is_finite() if isinstance(value, Decimal) else math.isfinite(value)):
            raise ValidationError("invalid_number", f"{path}: JSON numbers must be finite")
        return
    if not isinstance(value, (dict, list)):
        raise ValidationError("wrong_type", f"{path}: value is not JSON-compatible")
    ancestors = set() if ancestors is None else ancestors
    identity = id(value)
    if identity in ancestors:
        raise ValidationError("wrong_type", f"{path}: cyclic values are not JSON")
    ancestors.add(identity)
    try:
        if isinstance(value, dict):
            for key, item in value.items():
                if not isinstance(key, str):
                    raise ValidationError("wrong_type", f"{path}: JSON object keys must be strings")
                validate_json_value(item, f"{path}.{key}", ancestors)
        else:
            for index, item in enumerate(value):
                validate_json_value(item, f"{path}[{index}]", ancestors)
    finally:
        ancestors.remove(identity)


def parse_json(value: str | bytes | bytearray) -> Any:
    """Decode JSON exactly: integers become int; other tokens use Decimal/raw values.

    Duplicate decoded keys are rejected within each object, even for equal values.
    Use this at the initial wire boundary. Precision cannot be recovered from
    values already decoded by a binary-floating-point JSON parser. Schema
    decimal fields remain strings; Decimal represents ordinary JSON numbers.
    """
    def reject_constant(token: str) -> Any:
        raise ValidationError("invalid_number", f"JSON numbers must be finite: {token}")

    def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result = {}
        for key, item in pairs:
            if key in result:
                raise ValidationError("duplicate_key", f"Duplicate JSON key: {key!r}")
            result[key] = item
        return result

    # Decimal-to-int avoids CPython's configurable digit limit without changing
    # process-global security settings. The JSON decoder validates the grammar.
    return json.loads(value, parse_int=lambda token: int(Decimal(token)),
                      parse_float=parse_fraction, parse_constant=reject_constant,
                      object_pairs_hook=unique_object)


def stringify_json(value: Any, *, pretty: bool = False, sort_keys: bool = False) -> str:
    """Encode finite JSON data, including exact number values, without float coercion.

    Decimal coefficients and exponents are emitted directly as JSON numeric
    tokens, independently of the active decimal arithmetic context. Object
    keys, strings, booleans, null, and host float values use stdlib encoding.
    RawJsonNumber tokens retain their validated original spelling.
    """
    validate_json_value(value)

    def encode(item: Any, depth: int) -> str:
        if isinstance(item, RawJsonNumber):
            return item.token
        if isinstance(item, Decimal):
            return str(item)
        if isinstance(item, int) and not isinstance(item, bool):
            # Likewise avoid the host int-to-string digit limit for valid JSON.
            return str(Decimal(item))
        if not isinstance(item, (dict, list)):
            return json.dumps(item, ensure_ascii=False, allow_nan=False)
        is_object = isinstance(item, dict)
        opening, closing = ("{", "}") if is_object else ("[", "]")
        if not item:
            return opening + closing
        if is_object:
            keys = sorted(item) if sort_keys else item
            pieces = [json.dumps(key, ensure_ascii=False) + (": " if pretty else ":")
                      + encode(item[key], depth + 1) for key in keys]
        else:
            pieces = [encode(child, depth + 1) for child in item]
        if pretty:
            padding = "  " * (depth + 1)
            return opening + "\n" + padding + (",\n" + padding).join(pieces) + "\n" + "  " * depth + closing
        return opening + ",".join(pieces) + closing

    return encode(value, 0)


def validate_document(document: dict[str, Any], schema: dict | None = None) -> dict[str, Any]:
    if not isinstance(document, dict):
        raise ValidationError("wrong_type", "$: expected object")
    validate_json_value(document)
    if document.get("schemaVersion") != SPEC_VERSION:
        raise UnsupportedVersion(document.get("schemaVersion"))
    dtype = document.get("dtype")
    if not isinstance(dtype, str) or dtype not in DOCUMENT_TYPES:
        raise ValidationError("unknown_object_type", f"$.dtype: unknown document type {dtype!r}")
    schema = schema if schema is not None else load_schema()
    name = DOCUMENT_TYPES[dtype]
    # The release root is a definitions library. Select a concrete document;
    # validating the root alone would silently accept arbitrary objects.
    concrete = {**schema, "$ref": f"#/$defs/{name}"}
    validator = _EXACT_VALIDATOR(concrete, format_checker=FORMAT_CHECKER)
    errors = sorted(validator.iter_errors(document), key=lambda e: (tuple(map(str, e.absolute_path)), e.message))
    if errors:
        error = errors[0]
        path = "$" + "".join(f"[{p}]" if isinstance(p, int) else f".{p}" for p in error.absolute_path)
        raise ValidationError(category_for(error), f"{path}: {error.message}")
    decimal_constraints(document, {"$ref": f"#/$defs/{name}"}, schema)
    try:
        validate_operation_semantics(document)
        validate_workflow_semantics(document)
    except ValueError as error:
        raise ValidationError("operation_semantics", str(error)) from error
    # Construct through the actual generated TypedDict surface. It preserves
    # optional omission, false/null values, and opaque extension maps.
    getattr(generated, name)(**document)
    return document


def roundtrip_document(document: dict, schema: dict | None = None) -> dict:
    validate_document(document, schema)
    value = parse_json(stringify_json(document))
    validate_document(value, schema)
    return value


def schema_inventory(schema: dict | None = None) -> list[dict]:
    schema = schema if schema is not None else load_schema()
    return [{"object_type": dtype, "definition": name, "schema": schema["$defs"][name]}
            for dtype, name in sorted(DOCUMENT_TYPES.items())]


def capabilities(schema: dict | None = None) -> dict:
    return {"language": "python", "adapter_version": ADAPTER_VERSION,
            "spec_versions": [SPEC_VERSION], "authority": MANIFEST["library"],
            "commands": ["validate", "roundtrip", "version", "capabilities", "schema-inventory"],
            "object_types": sorted(DOCUMENT_TYPES), "preserves_unknown_extensions": True,
            "preserves_missing_optional_fields": True}


@dataclass(slots=True)
class Document:
    value: dict[str, Any]

    def __post_init__(self) -> None:
        # The public dataclass constructor is also a wire boundary. Do not allow
        # direct Document(value) to bypass the validated from_dict constructor.
        self.value = roundtrip_document(deepcopy(self.value))

    @classmethod
    def from_dict(cls, value: dict, schema: dict | None = None) -> Document:
        if schema is not None:
            roundtrip_document(value, schema)
        return cls(value)

    @classmethod
    def from_json(cls, value: str, schema: dict | None = None) -> Document:
        return cls.from_dict(parse_json(value), schema)

    def validate(self, schema: dict | None = None) -> Document:
        validate_document(self.value, schema)
        return self

    def to_dict(self) -> dict:
        # Revalidate mutable values at every public serialization boundary.
        return roundtrip_document(self.value)

    def to_json(self, *, pretty: bool = False) -> str:
        return stringify_json(self.to_dict(), pretty=pretty)

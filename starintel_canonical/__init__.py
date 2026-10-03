"""Runtime consumer of StarLang's immutable generated StarIntel release."""
from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

from ._release.generated import starintel_types as generated
from .errors import ValidationError, UnsupportedVersion
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


def definition_name(name: str) -> str:
    return "".join(part.capitalize() for part in name.rsplit("/", 1)[-1].split("-"))


DOCUMENT_TYPES = {
    entry["name"].rsplit("/", 1)[-1]: definition_name(entry["name"])
    for entry in MANIFEST["types"] if entry["kind"] == "document"
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
            if Draft202012Validator(candidate, format_checker=FORMAT_CHECKER).is_valid(value):
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


def validate_document(document: dict[str, Any], schema: dict | None = None) -> dict[str, Any]:
    if not isinstance(document, dict):
        raise ValidationError("wrong_type", "$: expected object")
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
    validator = Draft202012Validator(concrete, format_checker=FORMAT_CHECKER)
    errors = sorted(validator.iter_errors(document), key=lambda e: (tuple(map(str, e.absolute_path)), e.message))
    if errors:
        error = errors[0]
        path = "$" + "".join(f"[{p}]" if isinstance(p, int) else f".{p}" for p in error.absolute_path)
        raise ValidationError(category_for(error), f"{path}: {error.message}")
    decimal_constraints(document, {"$ref": f"#/$defs/{name}"}, schema)
    # Construct through the actual generated TypedDict surface. It preserves
    # optional omission, false/null values, and opaque extension maps.
    getattr(generated, name)(**document)
    return document


def roundtrip_document(document: dict, schema: dict | None = None) -> dict:
    validate_document(document, schema)
    value = json.loads(json.dumps(document, ensure_ascii=False, allow_nan=False))
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

    @classmethod
    def from_dict(cls, value: dict, schema: dict | None = None) -> Document:
        return cls(roundtrip_document(deepcopy(value), schema))

    @classmethod
    def from_json(cls, value: str, schema: dict | None = None) -> Document:
        return cls.from_dict(json.loads(value), schema)

    def validate(self, schema: dict | None = None) -> Document:
        validate_document(self.value, schema)
        return self

    def to_dict(self) -> dict:
        return deepcopy(self.value)

    def to_json(self, *, pretty: bool = False) -> str:
        return json.dumps(self.value, ensure_ascii=False, allow_nan=False, indent=2 if pretty else None)

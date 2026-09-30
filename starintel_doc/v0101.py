from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError as JsonSchemaValidationError


SPEC_VERSION = "0.10.1"
ADAPTER_VERSION = 2
SPEC_ROOT = Path(__file__).with_name("spec")


class ValidationError(ValueError):
    def __init__(self, category: str, message: str) -> None:
        super().__init__(message)
        self.category = category


class UnsupportedVersion(ValidationError):
    def __init__(self, value: Any) -> None:
        super().__init__("unsupportedSchemaVersion", f"unsupported schema version: {value!r}")


def load_schema() -> dict[str, Any]:
    value = json.loads((SPEC_ROOT / "schema.json").read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError("schema must be a JSON object")
    return value


def load_manifest() -> dict[str, Any]:
    value = json.loads((SPEC_ROOT / "portable-manifest.json").read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError("manifest must be a JSON object")
    return value


def document_definitions(manifest: dict[str, Any] | None = None) -> dict[str, str]:
    manifest = manifest or load_manifest()
    result: dict[str, str] = {}
    for contract in manifest.get("types", []):
        if contract.get("kind") != "document":
            continue
        dtype = contract["name"].rsplit("/", 1)[-1]
        result[dtype] = "".join(part.capitalize() for part in dtype.split("-"))
    return result


def _category(error: JsonSchemaValidationError) -> str:
    return {
        "required": "missingRequiredField",
        "additionalProperties": "undeclaredField",
        "minimum": "belowMinimum",
        "maximum": "aboveMaximum",
        "pattern": "patternMismatch",
        "enum": "invalidEnum",
        "const": "invalidConstant",
        "type": "wrongType",
        "anyOf": "wrongType",
    }.get(error.validator, "canonicalValidationFailed")


def validate_document(
    document: dict[str, Any],
    schema: dict[str, Any] | None = None,
    definitions: dict[str, str] | None = None,
) -> dict[str, Any]:
    if not isinstance(document, dict):
        raise ValidationError("wrongType", "$: expected object")
    if document.get("schemaVersion") != SPEC_VERSION:
        raise UnsupportedVersion(document.get("schemaVersion"))
    schema = schema or load_schema()
    definitions = definitions or document_definitions()
    dtype = document.get("dtype")
    definition = definitions.get(dtype) if isinstance(dtype, str) else None
    if definition is None or definition not in schema.get("$defs", {}):
        raise ValidationError("unknownObjectType", f"$.dtype: unknown document type {dtype!r}")
    selected = {
        "$schema": schema["$schema"],
        "$ref": f"#/$defs/{definition}",
        "$defs": schema["$defs"],
    }
    errors = sorted(
        Draft202012Validator(selected).iter_errors(document),
        key=lambda item: (tuple(map(str, item.absolute_path)), item.message),
    )
    if errors:
        error = errors[0]
        path = "$" + "".join(
            f"[{part}]" if isinstance(part, int) else f".{part}" for part in error.absolute_path
        )
        raise ValidationError(_category(error), f"{path}: {error.message}")
    return document


def roundtrip_document(document: dict[str, Any]) -> dict[str, Any]:
    validate_document(document)
    value = json.loads(json.dumps(document, ensure_ascii=False, separators=(",", ":")))
    validate_document(value)
    return value


@dataclass(slots=True)
class Document:
    value: dict[str, Any]

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "Document":
        return cls(roundtrip_document(deepcopy(value)))

    @classmethod
    def from_json(cls, value: str) -> "Document":
        parsed = json.loads(value)
        if not isinstance(parsed, dict):
            raise ValidationError("wrongType", "$: expected object")
        return cls.from_dict(parsed)

    def validate(self) -> "Document":
        validate_document(self.value)
        return self

    def to_dict(self) -> dict[str, Any]:
        return deepcopy(self.value)

    def to_json(self, *, pretty: bool = False) -> str:
        return json.dumps(
            self.value,
            ensure_ascii=False,
            indent=2 if pretty else None,
            separators=None if pretty else (",", ":"),
            sort_keys=True,
        )


def schema_inventory() -> list[dict[str, Any]]:
    schema = load_schema()
    return [
        {"dtype": dtype, "definition": definition}
        for dtype, definition in sorted(document_definitions().items())
        if definition in schema["$defs"]
    ]


def capabilities() -> dict[str, Any]:
    return {
        "language": "python",
        "adapterVersion": ADAPTER_VERSION,
        "specVersions": ["0.9.0", SPEC_VERSION],
        "emittedSpecVersion": SPEC_VERSION,
        "commands": [
            "validate",
            "normalize",
            "roundtrip",
            "migrate",
            "migrateBatch",
            "version",
            "capabilities",
            "schemaInventory",
        ],
        "objectTypes": sorted(document_definitions()),
        "preservesUnknownExtensions": True,
        "preservesMissingOptionalFields": True,
    }

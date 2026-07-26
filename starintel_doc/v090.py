from __future__ import annotations

import json
import os
from copy import deepcopy
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import ValidationError as JsonSchemaValidationError

SPEC_VERSION = "0.9.0"
ADAPTER_VERSION = 1
ALIASES = {
    "organization",
    "organisation",
    "investigation_target",
    "social_media_post",
    "email_message",
    "financial_observation",
    "research_pass",
    "dataset_manifest",
    "actor_manifest",
    "legal_case",
    "lobbying_filing",
    "campaign_finance",
}


class ValidationError(ValueError):
    def __init__(self, category: str, message: str) -> None:
        super().__init__(message)
        self.category = category


class UnsupportedVersion(ValidationError):
    def __init__(self, value: Any) -> None:
        super().__init__("unsupported_spec_version", f"unsupported spec version: {value!r}")


def schema_path() -> Path:
    explicit = os.environ.get("STARINTEL_SCHEMA")
    if explicit:
        return Path(explicit)
    root = os.environ.get("STARINTEL_CONFORMANCE_ROOT")
    if root:
        return Path(root) / "schemas" / "starintel-doc-v0.9.0.schema.json"
    return Path.cwd() / "schemas" / "starintel-doc-v0.9.0.schema.json"


def load_schema() -> dict[str, Any]:
    path = schema_path()
    if not path.is_file():
        raise FileNotFoundError(f"StarIntel schema not found: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError("schema must be a JSON object")
    return value


def dtype_schemas(schema: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for branch in schema.get("allOf", []):
        dtype = branch.get("if", {}).get("properties", {}).get("dtype", {}).get("const")
        data = branch.get("then", {}).get("properties", {}).get("data")
        if isinstance(dtype, str) and isinstance(data, dict):
            result[dtype] = data
    return result


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


def validate_document(document: dict[str, Any], schema: dict[str, Any] | None = None) -> dict[str, Any]:
    if not isinstance(document, dict):
        raise ValidationError("wrong_type", "$: expected object")
    if document.get("schema_version") != SPEC_VERSION:
        raise UnsupportedVersion(document.get("schema_version"))
    schema = schema or load_schema()
    types = dtype_schemas(schema)
    dtype = document.get("dtype")
    if isinstance(dtype, str) and dtype not in types:
        if dtype in ALIASES:
            raise ValidationError("invalid_enum", "$.dtype: alias is not canonical")
        raise ValidationError("unknown_object_type", f"$.dtype: unknown document type {dtype!r}")
    errors = sorted(
        Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(document),
        key=lambda item: (list(item.absolute_path), item.message),
    )
    if errors:
        error = errors[0]
        path = "$" + "".join(f"[{part}]" if isinstance(part, int) else f".{part}" for part in error.absolute_path)
        raise ValidationError(category_for(error), f"{path}: {error.message}")
    return document


def roundtrip_document(document: dict[str, Any], schema: dict[str, Any] | None = None) -> dict[str, Any]:
    schema = schema or load_schema()
    validate_document(document, schema)
    value = json.loads(json.dumps(document, ensure_ascii=False, separators=(",", ":")))
    validate_document(value, schema)
    return value


def schema_inventory(schema: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    schema = schema or load_schema()
    inventory: list[dict[str, Any]] = []
    for dtype, data in sorted(dtype_schemas(schema).items()):
        required = set(data.get("required", []))
        fields: dict[str, Any] = {}
        for name, definition in sorted(data.get("properties", {}).items()):
            item: dict[str, Any] = {"required": name in required}
            if "type" in definition:
                item["type"] = definition["type"]
            if "anyOf" in definition:
                item["any_of"] = [candidate.get("type", candidate.get("const", "any")) for candidate in definition["anyOf"]]
            if "enum" in definition:
                item["enum"] = definition["enum"]
            if "format" in definition:
                item["format"] = definition["format"]
            fields[name] = item
        inventory.append({"object_type": dtype, "fields": fields})
    return inventory


def capabilities(schema: dict[str, Any] | None = None) -> dict[str, Any]:
    schema = schema or load_schema()
    return {
        "language": "python",
        "adapter_version": ADAPTER_VERSION,
        "spec_versions": [SPEC_VERSION],
        "commands": ["validate", "normalize", "roundtrip", "version", "capabilities", "schema-inventory"],
        "object_types": sorted(dtype_schemas(schema)),
        "preserves_unknown_extensions": True,
        "preserves_missing_optional_fields": True,
    }

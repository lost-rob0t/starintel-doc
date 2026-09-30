from __future__ import annotations

import hashlib
import json
import re
from copy import deepcopy
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from .v0101 import SPEC_ROOT, SPEC_VERSION, document_definitions, load_schema, validate_document


SNAKE_PART = re.compile(r"_([a-z0-9])")


class MigrationError(ValueError):
    def __init__(self, reason_code: str, message: str) -> None:
        super().__init__(message)
        self.reason_code = reason_code


def load_compatibility() -> dict[str, Any]:
    return json.loads((SPEC_ROOT / "compatibility.json").read_text(encoding="utf-8"))


def load_compatibility_fixtures() -> dict[str, Any]:
    return json.loads((SPEC_ROOT / "compatibility-fixtures.json").read_text(encoding="utf-8"))


def _camel(name: str) -> str:
    return SNAKE_PART.sub(lambda match: match.group(1).upper(), name)


def _normalized_object(
    value: dict[str, Any],
    aliases: dict[str, str],
    opaque_fields: set[str],
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for source, item in value.items():
        target = aliases.get(source, _camel(source))
        if target in result:
            raise MigrationError(
                "ambiguousFieldCollision",
                f"both {source!r} and another field normalize to {target!r}",
            )
        if target in opaque_fields:
            result[target] = deepcopy(item)
        elif isinstance(item, dict):
            result[target] = _normalized_object(item, aliases, opaque_fields)
        elif isinstance(item, list):
            result[target] = [
                _normalized_object(entry, aliases, opaque_fields) if isinstance(entry, dict) else deepcopy(entry)
                for entry in item
            ]
        else:
            result[target] = deepcopy(item)
    return result


def _merge_legacy_data(document: dict[str, Any]) -> None:
    data = document.pop("data", None)
    if data is None:
        return
    if not isinstance(data, dict):
        raise MigrationError("migrationFailed", "legacy data must be an object")
    for key, value in data.items():
        if key in document:
            raise MigrationError("ambiguousFieldCollision", f"legacy data collides at {key!r}")
        document[key] = value


def _classify_media(document: dict[str, Any], policy: dict[str, Any]) -> None:
    if document.get("dtype") != policy["legacyDtype"]:
        return
    media_type = None
    for field in policy["contentTypePrecedence"]:
        candidate = document.get(field)
        if isinstance(candidate, str) and candidate:
            media_type = candidate.lower()
            break
    document["dtype"] = policy["fallbackDtype"]
    if media_type:
        for rule in policy["rules"]:
            if media_type.startswith(rule["prefix"]):
                document["dtype"] = rule["dtype"]
                break


def _convert_geo(document: dict[str, Any], policy: dict[str, Any]) -> None:
    if document.get("dtype") != policy["legacyDtype"]:
        return
    aliases = {_camel(source): target for source, target in policy["fieldAliases"].items()}
    for source, target in aliases.items():
        if source not in document:
            continue
        if target in document:
            raise MigrationError("ambiguousFieldCollision", f"geo field collides at {target!r}")
        document[target] = document.pop(source)
    document["dtype"] = policy["canonicalDtype"]
    for key, value in policy["defaults"].items():
        document.setdefault(key, value)
    try:
        longitude = Decimal(str(document["longitude"]))
        latitude = Decimal(str(document["latitude"]))
    except (KeyError, InvalidOperation) as exc:
        raise MigrationError("migrationFailed", "legacy geo requires decimal lat and long") from exc
    if not Decimal("-180") <= longitude <= Decimal("180"):
        raise MigrationError("canonicalValidationFailed", "longitude is outside [-180, 180]")
    if not Decimal("-90") <= latitude <= Decimal("90"):
        raise MigrationError("canonicalValidationFailed", "latitude is outside [-90, 90]")


def _reference(dtype: str, identifier: str) -> dict[str, str]:
    return {"schema": f"org.starintel/core@1/{dtype}", "id": identifier}


def _digest_id(prefix: str, parts: list[str]) -> str:
    encoded = "\0".join([prefix, *parts]).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _extract_person_identifiers(document: dict[str, Any]) -> list[dict[str, Any]]:
    if document.get("dtype") != "person" or not isinstance(document.get("externalIds"), dict):
        return []
    generated: list[dict[str, Any]] = []
    references: list[dict[str, str]] = []
    for scheme, raw_value in sorted(document["externalIds"].items()):
        if not isinstance(raw_value, (str, int)):
            continue
        value = str(raw_value)
        normalized = value.strip().lower()
        identifier = "starintel:person-identifier:" + _digest_id(
            "personIdentifier", [document["id"], scheme, normalized]
        )
        references.append(_reference("person-identifier", identifier))
        generated.append(
            {
                "id": identifier,
                "dataset": document["dataset"],
                "dtype": "person-identifier",
                "schemaVersion": SPEC_VERSION,
                "person": _reference("person", document["id"]),
                "scheme": scheme,
                "value": value,
                "normalizedValue": normalized,
            }
        )
    if references:
        document["identifiers"] = references
    return generated


def _extract_transcript(document: dict[str, Any]) -> list[dict[str, Any]]:
    text = None
    for field in ("transcript", "transcriptText"):
        candidate = document.get(field)
        if isinstance(candidate, str) and candidate:
            text = candidate
            document.pop(field)
            break
    if text is None:
        return []
    language = str(document.get("language", ""))
    identifier = "starintel:transcript:" + _digest_id(
        "transcript", [document["id"], language]
    )
    reference = _reference("transcript", identifier)
    if document.get("dtype") == "audio":
        document["transcripts"] = [reference]
    else:
        document["transcript"] = reference
    transcript = {
        "id": identifier,
        "dataset": document["dataset"],
        "dtype": "transcript",
        "schemaVersion": SPEC_VERSION,
        "sourceMedia": _reference(document["dtype"], document["id"]),
        "text": text,
    }
    if language:
        transcript["language"] = language
    return [transcript]


def _preserve_unknown(document: dict[str, Any], schema: dict[str, Any], definitions: dict[str, str]) -> None:
    definition = definitions.get(document.get("dtype"))
    if definition is None or definition not in schema["$defs"]:
        raise MigrationError("canonicalValidationFailed", f"unknown dtype: {document.get('dtype')!r}")
    known = set(schema["$defs"][definition].get("properties", {}))
    unknown = {key: document.pop(key) for key in list(document) if key not in known}
    if not unknown:
        return
    extensions = document.setdefault("extensions", {})
    if not isinstance(extensions, dict):
        raise MigrationError("ambiguousFieldCollision", "extensions is not an object")
    if "legacy" in extensions:
        raise MigrationError("ambiguousFieldCollision", "extensions.legacy already exists")
    extensions["legacy"] = unknown


def migrate_document(value: dict[str, Any]) -> list[dict[str, Any]]:
    if not isinstance(value, dict):
        raise MigrationError("decodeFailed", "document must be an object")
    policy = load_compatibility()
    legacy = policy["legacyInput"]
    document = _normalized_object(
        value,
        legacy["envelopeAliases"],
        set(legacy["opaqueMapFields"]),
    )
    version = document.get("schemaVersion")
    if version not in policy["acceptedSchemaVersions"]:
        raise MigrationError("unsupportedSchemaVersion", f"unsupported schema version: {version!r}")
    _merge_legacy_data(document)
    dtype = document.get("dtype")
    if dtype in policy["dtypeAliases"]:
        document["dtype"] = policy["dtypeAliases"][dtype]
    _classify_media(document, policy["mediaClassification"])
    _convert_geo(document, policy["geo"])
    document["schemaVersion"] = SPEC_VERSION

    generated = _extract_person_identifiers(document)
    generated.extend(_extract_transcript(document))
    documents = [document, *generated]
    schema = load_schema()
    definitions = document_definitions()
    for migrated in documents:
        _preserve_unknown(migrated, schema, definitions)
        try:
            validate_document(migrated, schema, definitions)
        except Exception as exc:
            if isinstance(exc, MigrationError):
                raise
            raise MigrationError("canonicalValidationFailed", str(exc)) from exc
    return documents


def migrate_batch(values: list[Any]) -> dict[str, list[dict[str, Any]]]:
    documents: list[dict[str, Any]] = []
    quarantine: list[dict[str, Any]] = []
    for value in values:
        try:
            documents.extend(migrate_document(value))
        except MigrationError as exc:
            quarantine.append({"reasonCode": exc.reason_code})
        except Exception:
            quarantine.append({"reasonCode": "migrationFailed"})
    return {"documents": documents, "quarantine": quarantine}

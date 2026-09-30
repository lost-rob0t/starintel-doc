from __future__ import annotations

import json
import sys
from typing import Any

from .v0101 import (
    ADAPTER_VERSION,
    SPEC_VERSION,
    UnsupportedVersion,
    ValidationError,
    capabilities,
    load_schema,
    roundtrip_document,
    schema_inventory,
    validate_document,
)
from .migration import MigrationError, migrate_batch, migrate_document


def emit(value: dict[str, Any]) -> None:
    print(json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True))


def main() -> int:
    try:
        request = json.load(sys.stdin)
        if not isinstance(request, dict):
            raise TypeError("request must be a JSON object")
        command = request.get("command")
        if command == "version":
            emit({"ok": True, "language": "python", "specVersion": SPEC_VERSION, "adapterVersion": ADAPTER_VERSION})
            return 0

        requested = request.get("specVersion", request.get("spec_version", SPEC_VERSION))
        if requested not in {"0.9.0", SPEC_VERSION}:
            raise UnsupportedVersion(requested)

        if command == "capabilities":
            emit({"ok": True, **capabilities()})
            return 0
        if command in {"schemaInventory", "schema-inventory"}:
            emit({"ok": True, "specVersion": SPEC_VERSION, "inventory": schema_inventory()})
            return 0

        document = request.get("document")
        if command == "validate":
            validate_document(document)
            emit({"ok": True, "specVersion": SPEC_VERSION, "warnings": []})
            return 0
        if command in {"normalize", "roundtrip"}:
            value = roundtrip_document(document)
            emit({"ok": True, "specVersion": SPEC_VERSION, "document": value, "warnings": []})
            return 0
        if command == "migrate":
            emit({"ok": True, "specVersion": SPEC_VERSION, "documents": migrate_document(document)})
            return 0
        if command == "migrateBatch":
            result = migrate_batch(request.get("documents", []))
            emit({"ok": True, "specVersion": SPEC_VERSION, **result})
            return 0
        raise ValueError(f"unsupported command: {command!r}")
    except UnsupportedVersion as exc:
        emit({"ok": False, "error": exc.category, "message": str(exc)})
        return 3
    except ValidationError as exc:
        emit({"ok": False, "error": exc.category, "message": str(exc)})
        return 1
    except MigrationError as exc:
        emit({"ok": False, "error": exc.reason_code, "message": str(exc)})
        return 1
    except Exception as exc:
        print(f"python adapter failure: {exc}", file=sys.stderr)
        emit({"ok": False, "error": "adapter_failure", "message": str(exc)})
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

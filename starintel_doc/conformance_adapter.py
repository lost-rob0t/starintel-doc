from __future__ import annotations

import json
import sys
from typing import Any

from .compat import migrate_compatible_document
from .v0101 import (
    ACCEPTED_SPEC_VERSIONS,
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


def emit(value: dict[str, Any]) -> None:
    print(json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True))


def main() -> int:
    try:
        request = json.load(sys.stdin)
        if not isinstance(request, dict):
            raise TypeError("request must be a JSON object")
        command = request.get("command")
        if command == "version":
            emit({
                "ok": True,
                "language": "python",
                "spec_version": SPEC_VERSION,
                "accepted_spec_versions": sorted(ACCEPTED_SPEC_VERSIONS),
                "adapter_version": ADAPTER_VERSION,
            })
            return 0

        requested = request.get("spec_version", SPEC_VERSION)
        if command != "migrate" and requested not in ACCEPTED_SPEC_VERSIONS:
            raise UnsupportedVersion(requested)

        schema = load_schema()
        if command == "capabilities":
            emit({"ok": True, **capabilities(schema)})
            return 0
        if command == "schema-inventory":
            emit({"ok": True, "spec_version": SPEC_VERSION, "inventory": schema_inventory(schema)})
            return 0

        document = request.get("document")
        if command == "migrate":
            value = migrate_compatible_document(
                document,
                original_uri=str(request.get("original_uri") or ""),
                schema=schema,
            )
            emit({"ok": True, "spec_version": SPEC_VERSION, "document": value, "warnings": []})
            return 0
        if command == "validate":
            validate_document(document, schema)
            emit({"ok": True, "spec_version": requested, "warnings": []})
            return 0
        if command in {"normalize", "roundtrip"}:
            value = roundtrip_document(document, schema)
            emit({"ok": True, "spec_version": requested, "document": value, "warnings": []})
            return 0
        raise ValueError(f"unsupported command: {command!r}")
    except UnsupportedVersion as exc:
        emit({"ok": False, "error": exc.category, "message": str(exc)})
        return 3
    except ValidationError as exc:
        emit({"ok": False, "error": exc.category, "message": str(exc)})
        return 1
    except Exception as exc:
        print(f"python adapter failure: {exc}", file=sys.stderr)
        emit({"ok": False, "error": "adapter_failure", "message": str(exc)})
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

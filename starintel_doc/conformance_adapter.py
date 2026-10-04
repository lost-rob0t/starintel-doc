from __future__ import annotations

import json
import sys
from typing import Any

from .canonical import (
    ADAPTER_VERSION,
    SPEC_VERSION,
    UnsupportedVersion,
    ValidationError,
    capabilities,
    load_schema,
    parse_json,
    stringify_json,
    roundtrip_document,
    schema_inventory,
    validate_document,
)


def emit(value: dict[str, Any]) -> None:
    print(stringify_json(value, sort_keys=True))


def main() -> int:
    try:
        request_text = sys.stdin.read()
        request = parse_json(request_text)
        if not isinstance(request, dict):
            raise TypeError("request must be a JSON object")
        command = request.get("command")
        if command == "version":
            requested = request.get("spec_version", SPEC_VERSION)
            if requested not in {SPEC_VERSION, "0.9.0"}:
                raise UnsupportedVersion(requested)
            emit({"ok": True, "language": "python", "spec_version": requested, "adapter_version": ADAPTER_VERSION})
            return 0

        requested = request.get("spec_version", SPEC_VERSION)
        if requested == "0.9.0":
            # Historical compatibility is selected explicitly by the caller.
            from . import v090 as runtime
            request = json.loads(request_text)
        elif requested == SPEC_VERSION:
            from . import canonical as runtime
        else:
            raise UnsupportedVersion(requested)
        schema = runtime.load_schema()
        if command == "capabilities":
            emit({"ok": True, **runtime.capabilities(schema)})
            return 0
        if command == "schema-inventory":
            emit({"ok": True, "spec_version": requested, "inventory": runtime.schema_inventory(schema)})
            return 0

        document = request.get("document")
        if command == "validate":
            runtime.validate_document(document, schema)
            emit({"ok": True, "spec_version": requested, "warnings": []})
            return 0
        if command in {"normalize", "roundtrip"}:
            value = runtime.roundtrip_document(document, schema)
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

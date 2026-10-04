"""Explicit historical nested-envelope compatibility; current wire never coerces.

The original envelope/payload is retained under extensions.legacy when it cannot
be represented directly. Unknown dtypes, collisions, and ambiguous references
fail closed. This adapter does not create related entities or infer identities.
"""
from __future__ import annotations
from copy import deepcopy
from datetime import datetime
from decimal import Decimal, InvalidOperation
import json
import math
from typing import Any
from pathlib import Path
from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import ValidationError as SchemaValidationError

from . import DOCUMENT_TYPES, RELEASE_ROOT, load_schema, validate_document, decimal_constraints, stringify_json

_LEGACY = json.loads((Path(__file__).parent / "_compatibility/shared-legacy-oracle.json").read_text())["schemas"]
_FORMAT = FormatChecker()


def camel(key: str) -> str:
    head, *tail = key.split('_')
    return head + ''.join(part[:1].upper() + part[1:] for part in tail)


def reference(value: Any, dtype_registry: dict[str, str]) -> dict:
    if isinstance(value, dict):
        if set(value) == {'schema', 'id'}:
            return deepcopy(value)
        dtype = value.get('dtype')
        identity = value.get('id')
        if dtype in DOCUMENT_TYPES and isinstance(identity, str):
            return {'schema': 'org.starintel/core@1/' + dtype, 'id': identity}
        raise ValueError('ambiguous legacy reference: requires explicit schema/id or known dtype/id')
    if isinstance(value, str) and dtype_registry.get(value) in DOCUMENT_TYPES:
        return {'schema': 'org.starintel/core@1/' + dtype_registry[value], 'id': value}
    raise ValueError('ambiguous legacy reference: no canonical dtype identity')


def convert(value: Any, node: dict, schema: dict, dtype_registry: dict[str, str]) -> Any:
    if '$ref' in node:
        name = node['$ref'].rsplit('/', 1)[-1]
        if name == 'StarReference':
            return reference(value, dtype_registry)
        if name == 'UnixTime' and isinstance(value, str):
            moment = datetime.fromisoformat(value.replace('Z', '+00:00'))
            if moment.tzinfo is None:
                raise ValueError('timestamp timezone required')
            return int(moment.timestamp())
        return convert(value, schema['$defs'][name], schema, dtype_registry)
    if 'anyOf' in node:
        if value is None and any(x.get('type') == 'null' for x in node['anyOf']):
            return None
        errors = []
        for branch in node['anyOf']:
            if branch.get('type') == 'null':
                continue
            try:
                return convert(value, branch, schema, dtype_registry)
            except (ValueError, TypeError) as error:
                errors.append(str(error))
        raise ValueError('; '.join(errors))
    if node.get('type') == 'string' and node.get('pattern') == '^[+-]?[0-9]+(?:\\.[0-9]+)?$':
        if isinstance(value, bool) or not isinstance(value, (str, int, float, Decimal)):
            raise ValueError('decimal requires a finite numeric value')
        number = Decimal(str(value))
        if not number.is_finite():
            raise ValueError('decimal must be finite')
        return format(number, 'f')
    if node.get('type') == 'array':
        items = node.get('items', {})
        target = schema['$defs'].get(items.get('$ref', '').rsplit('/', 1)[-1], items)
        # Generated typed dynamic maps use explicit key/value entry arrays.
        if isinstance(value, dict) and set(target.get('properties', {})) == {'key', 'value'}:
            return [{'key': key, 'value': convert(item, target['properties']['value'], schema, dtype_registry)}
                    for key, item in value.items()]
        if not isinstance(value, list):
            raise ValueError('array required')
        return [convert(item, items, schema, dtype_registry) for item in value]
    if node.get('type') == 'object':
        if not isinstance(value, dict):
            raise ValueError('object required')
        props = node.get('properties')
        if props is None:
            return deepcopy(value)  # declared opaque map: keys are not field names
        result = {}
        for key, item in value.items():
            wire = key if key in props else camel(key)
            if wire in result:
                raise ValueError('ambiguous normalized field collision: ' + wire)
            if wire not in props:
                raise ValueError('undeclared structured field: ' + key)
            result[wire] = convert(item, props[wire], schema, dtype_registry)
        return result
    return deepcopy(value)


def canonicalize_document(document: dict, *, dtype_registry: dict[str, str] | None = None) -> dict:
    try:
        stringify_json(document)
    except (TypeError, ValueError) as error:
        raise ValueError("migration requires finite JSON document values") from error
    dtype_registry = dtype_registry or {}
    if not isinstance(document, dict):
        raise ValueError('document must be an object')
    if not isinstance(document.get('data', {}), dict):
        raise ValueError('legacy data must be an object')
    if not isinstance(document.get('handling', {}), dict):
        raise ValueError('legacy handling must be an object')
    if not isinstance(document.get('extensions', {}), dict):
        raise ValueError('extensions must be an object')
    if 'schemaVersion' in document:
        value = deepcopy(document)
        validate_document(value)
        return value
    if document.get('schema_version') not in {'0.9.0', '0.10.1'}:
        raise ValueError('unsupported historical schema_version')
    dtype = document.get('dtype')
    if dtype not in DOCUMENT_TYPES:
        raise ValueError('no canonical dtype mapping: ' + str(dtype))
    schema = load_schema()
    props = schema['$defs'][DOCUMENT_TYPES[dtype]]['properties']
    mapping_path = RELEASE_ROOT / 'supported-workflow-mappings.json'
    mappings = json.loads(mapping_path.read_text())['contracts'] if mapping_path.exists() else {}
    field_map = mappings.get(dtype, {}).get('fields', {})
    aliases = {'relation': {'subject': 'source', 'object': 'destination', 'target': 'destination'},
               'message': {'content': 'message', 'author_id': 'user'},
               'person': {'name': 'fullName'}, 'domain': {'domain': 'name'}}.get(dtype, {})
    value = {'id': document.get('_id'), 'dataset': document.get('dataset'),
             'dtype': dtype, 'schemaVersion': '0.10.1'}
    original = {key: deepcopy(item) for key, item in document.items()
                if key not in {'_id', 'dataset', 'dtype', 'schema_version', 'extensions'}}
    envelope = {'_rev': 'rev', 'date_added': 'createdAt', 'date_updated': 'updatedAt'}
    envelope_props = schema['$defs']['Document']['properties']
    for key, item in document.items():
        if key in {'_id', 'dataset', 'dtype', 'schema_version', 'data', 'extensions', 'sources'}:
            continue
        wire = envelope.get(key, camel(key))
        if wire in envelope_props:
            if wire in value:
                raise ValueError('ambiguous normalized envelope collision: ' + wire)
            if wire == 'notes' and isinstance(item, list):
                continue  # original list retained verbatim; never join lossily
            value[wire] = convert(item, envelope_props[wire], schema, dtype_registry)
    handling = document.get('handling', {})
    if handling:
        if not isinstance(handling, dict):
            raise ValueError('legacy handling must be an object')
        if 'visibility' in handling:
            if 'visibility' in value and value['visibility'] != handling['visibility']:
                raise ValueError('conflicting handling visibility')
            value['visibility'] = handling['visibility']
        # Preserve the complete policy in an explicit access-control map. This
        # is data preservation, not a claim that every consumer enforces it.
        value.setdefault('accessControl', {})['legacyHandling'] = deepcopy(handling)
    sources = document.get('sources', [])
    canonical_sources = []
    urls = []
    for item in sources:
        if isinstance(item, dict) and isinstance(item.get('url'), str):
            urls.append(item['url'])
        elif isinstance(item, dict) and not ({'id', 'schema', 'dtype'} & set(item)):
            continue  # optional source description is retained verbatim in original.sources
        else:
            canonical_sources.append(reference(item, dtype_registry))
    if canonical_sources:
        value['sources'] = canonical_sources
    if urls:
        value['sourceUrls'] = list(dict.fromkeys([*value.get('sourceUrls', []), *urls]))
    retained_fields = []
    required_fields = schema['$defs'][DOCUMENT_TYPES[dtype]].get('required', [])
    for key, item in document.get('data', {}).items():
        if dtype == 'person' and key == 'name' and 'full_name' in document.get('data', {}):
            continue  # preserve observed label; explicit full_name supplies native fullName
        wire = field_map.get(key, aliases.get(key, camel(key)))
        if wire in value:
            raise ValueError('ambiguous envelope/payload collision: ' + wire)
        if wire in props:
            try:
                candidate = convert(item, props[wire], schema, dtype_registry)
                Draft202012Validator({**schema, **props[wire]}, format_checker=_FORMAT).validate(candidate)
                decimal_constraints(candidate, props[wire], schema)
            except (ValueError, TypeError, InvalidOperation, SchemaValidationError):
                old_field = _LEGACY.get(dtype, {}).get('properties', {}).get(key)
                if wire in required_fields or old_field is None:
                    raise
                # Preserve only values proven valid under the pinned legacy field
                # contract; do not launder malformed input through compatibility.
                Draft202012Validator(old_field, format_checker=_FORMAT).validate(item)
                retained_fields.append({'field': key, 'reason': 'legacy_value_not_native'})
                continue
            value[wire] = candidate
        else:
            retained_fields.append({'field': key, 'reason': 'no_native_field'})
    extensions = deepcopy(document.get('extensions', {}))
    if original:
        if 'legacy' in extensions:
            raise ValueError('legacy preservation collision')
        extensions['legacy'] = {'schemaVersion': document['schema_version'], 'original': original}
        if retained_fields:
            extensions['legacy']['unmappedDataFields'] = retained_fields
    if extensions:
        value['extensions'] = extensions
    validate_document(value)
    return value

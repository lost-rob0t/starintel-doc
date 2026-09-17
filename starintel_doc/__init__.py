#!/usr/bin/env python3

from starintel_doc.v090 import (
    ADAPTER_VERSION,
    SPEC_VERSION,
    Document,
    UnsupportedVersion,
    ValidationError,
    capabilities,
    load_schema,
    roundtrip_document,
    schema_inventory,
    validate_document,
)
from starintel_doc.network_capture import (
    NETWORK_CAPTURE_DTYPES,
    PROFILE_VERSION,
    RELEASE_VERSION,
    build_http_transaction,
    build_web_capture,
    profile_schema,
    redact_headers,
    to_jsonld as network_capture_to_jsonld,
)

# Legacy flat 0.8 modules remain importable for explicit migration work.
from starintel_doc import documents as legacy_documents
from starintel_doc import entities as legacy_entities
from starintel_doc import hosts as legacy_hosts
from starintel_doc import locations as legacy_locations
from starintel_doc import manifest as legacy_manifest
from starintel_doc import phones as legacy_phones
from starintel_doc import relations as legacy_relations
from starintel_doc import social_media as legacy_social_media
from starintel_doc import targets as legacy_targets
from starintel_doc import web as legacy_web

__all__ = [
    "ADAPTER_VERSION",
    "SPEC_VERSION",
    "Document",
    "NETWORK_CAPTURE_DTYPES",
    "PROFILE_VERSION",
    "RELEASE_VERSION",
    "UnsupportedVersion",
    "ValidationError",
    "build_http_transaction",
    "build_web_capture",
    "capabilities",
    "load_schema",
    "network_capture_to_jsonld",
    "profile_schema",
    "redact_headers",
    "roundtrip_document",
    "schema_inventory",
    "validate_document",
]

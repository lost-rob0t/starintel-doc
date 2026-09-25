#!/usr/bin/env python3

from starintel_doc.v0101 import (
    ACCEPTED_SPEC_VERSIONS,
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
from starintel_doc.compat import LEGACY_FLAT_VERSIONS, migrate_compatible_document
from starintel_doc.artifacts import (
    ARTIFACT_EXTENSION,
    WIRELESS_SECURITY_VALUES,
    build_file_document,
    build_image_document,
    build_pcap_capture_document,
    build_video_document,
    build_video_frame_document,
    build_wireless_network_document,
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

# Old implementations remain importable for explicit compatibility work.
from starintel_doc import v090 as legacy_v090
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
    "ACCEPTED_SPEC_VERSIONS",
    "ADAPTER_VERSION",
    "ARTIFACT_EXTENSION",
    "SPEC_VERSION",
    "Document",
    "LEGACY_FLAT_VERSIONS",
    "NETWORK_CAPTURE_DTYPES",
    "PROFILE_VERSION",
    "RELEASE_VERSION",
    "UnsupportedVersion",
    "ValidationError",
    "WIRELESS_SECURITY_VALUES",
    "build_file_document",
    "build_http_transaction",
    "build_image_document",
    "build_pcap_capture_document",
    "build_video_document",
    "build_video_frame_document",
    "build_web_capture",
    "build_wireless_network_document",
    "capabilities",
    "load_schema",
    "migrate_compatible_document",
    "network_capture_to_jsonld",
    "profile_schema",
    "redact_headers",
    "roundtrip_document",
    "schema_inventory",
    "validate_document",
]

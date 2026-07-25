#!/usr/bin/env python3
from __future__ import annotations

import inspect
from types import ModuleType

from starintel_doc import documents
from starintel_doc import entities
from starintel_doc import locations
from starintel_doc import web
from starintel_doc import social_media
from starintel_doc import hosts
from starintel_doc import phones
from starintel_doc import targets
from starintel_doc import relations
from starintel_doc import manifest
from starintel_doc.documents import Document, STARINTEL_DOC_VERSION, utc_now
from starintel_doc.schema_org import (
    CANONICAL_DTYPES,
    DTYPE_ALIASES,
    DTYPE_SCHEMA_ORG_TYPES,
    SCHEMA_ORG_CONTEXT,
    canonical_dtype,
    schema_org_metadata,
    schema_org_types,
    to_schema_org,
)


def _document_classes(module: ModuleType):
    for value in vars(module).values():
        if not inspect.isclass(value):
            continue
        try:
            if issubclass(value, Document):
                yield value
        except TypeError:
            continue


def _install_v09_serializers() -> None:
    """Override legacy dataclasses-json serializers with the canonical v0.9 wire codec."""
    modules = (
        documents,
        entities,
        locations,
        web,
        social_media,
        hosts,
        phones,
        targets,
        relations,
        manifest,
    )
    classes = {document_class for module in modules for document_class in _document_classes(module)}
    for document_class in classes:
        document_class.asdict = Document.asdict
        document_class.to_dict = Document.to_dict
        document_class.to_json = Document.to_json
        document_class.to_schema_org = Document.to_schema_org


_install_v09_serializers()

__all__ = [
    "CANONICAL_DTYPES",
    "DTYPE_ALIASES",
    "DTYPE_SCHEMA_ORG_TYPES",
    "Document",
    "SCHEMA_ORG_CONTEXT",
    "STARINTEL_DOC_VERSION",
    "canonical_dtype",
    "documents",
    "entities",
    "hosts",
    "locations",
    "manifest",
    "phones",
    "relations",
    "schema_org_metadata",
    "schema_org_types",
    "social_media",
    "targets",
    "to_schema_org",
    "utc_now",
    "web",
]

#!/usr/bin/env python3
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any

import ulid
from dataclasses_json import config

from starintel_doc.schema_org import canonical_dtype, schema_org_metadata, to_schema_org

STARINTEL_DOC_VERSION = "0.9.0"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _source_values(values: list[Any]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for value in values:
        if isinstance(value, str):
            normalized.append({"kind": "web", "url": value, "uri": value, "name": value})
        elif isinstance(value, dict):
            normalized.append(value)
        else:
            normalized.append({"kind": "unknown", "metadata": {"value": value}})
    return normalized


@dataclass
class Document:
    """Canonical StarIntel v0.9 document with legacy subclass compatibility."""

    id: str = field(kw_only=True, default="", metadata=config(field_name="_id"))
    rev: str | None = field(kw_only=True, default=None, metadata=config(field_name="_rev"))
    dataset: str = field(kw_only=True, default="star-intel")
    dtype: str = field(kw_only=True, default="document")
    schema_version: str = field(kw_only=True, default=STARINTEL_DOC_VERSION)
    version: int = field(kw_only=True, default=1)
    date_added: str = field(kw_only=True, default_factory=utc_now)
    date_updated: str = field(kw_only=True, default_factory=utc_now)
    title: str = field(kw_only=True, default="")
    summary: str = field(kw_only=True, default="")
    description: str = field(kw_only=True, default="")
    status: str = field(kw_only=True, default="recorded")
    language: str = field(kw_only=True, default="en")
    tags: list[str] = field(kw_only=True, default_factory=list)
    labels: list[str] = field(kw_only=True, default_factory=list)
    aliases: list[str] = field(kw_only=True, default_factory=list)
    keywords: list[str] = field(kw_only=True, default_factory=list)
    identifiers: list[dict[str, Any]] = field(kw_only=True, default_factory=list)
    sources: list[Any] = field(kw_only=True, default_factory=list)
    evidence: list[dict[str, Any]] = field(kw_only=True, default_factory=list)
    temporal: dict[str, Any] = field(kw_only=True, default_factory=dict)
    provenance: dict[str, Any] = field(kw_only=True, default_factory=dict)
    assessment: dict[str, Any] = field(kw_only=True, default_factory=dict)
    verification: dict[str, Any] = field(
        kw_only=True,
        default_factory=lambda: {"status": "unverified", "verified": False},
    )
    handling: dict[str, Any] = field(
        kw_only=True,
        default_factory=lambda: {"visibility": "public", "sensitive": False, "pii": False},
    )
    lineage: dict[str, Any] = field(kw_only=True, default_factory=dict)
    quality: dict[str, Any] = field(kw_only=True, default_factory=dict)
    workflow: dict[str, Any] = field(kw_only=True, default_factory=dict)
    geospatial: dict[str, Any] = field(kw_only=True, default_factory=dict)
    attachments: list[dict[str, Any]] = field(kw_only=True, default_factory=list)
    related_ids: list[str] = field(kw_only=True, default_factory=list)
    notes: list[str] = field(kw_only=True, default_factory=list)
    schema_org: dict[str, Any] = field(kw_only=True, default_factory=dict)
    data: dict[str, Any] = field(kw_only=True, default_factory=dict)
    extensions: dict[str, Any] = field(kw_only=True, default_factory=dict)

    def ulid_id(self) -> None:
        self.id = str(ulid.new())

    def timestamp(self) -> None:
        now = utc_now()
        if not self.date_added:
            self.date_added = now
        if not self.date_updated:
            self.date_updated = now

    def update_timestamp(self) -> None:
        self.date_updated = utc_now()

    def update_timetamp(self) -> None:
        self.update_timestamp()

    def set_id(self) -> None:
        if not self.id:
            self.ulid_id()

    def set_type(self) -> None:
        self.dtype = canonical_dtype(self.__class__.__name__)

    def set_meta(self, dataset: str) -> "Document":
        self.dataset = dataset
        self.set_type()
        self.set_id()
        self._refresh_schema_org()
        return self

    def hash_id(self, *values: Any) -> None:
        raw = "\x1f".join(json.dumps(value, ensure_ascii=False, sort_keys=True) for value in values)
        self.id = sha256(raw.encode("utf-8")).hexdigest()

    def touch(self, *, updated_by: str = "") -> "Document":
        self.version = max(1, int(self.version)) + 1
        self.date_updated = utc_now()
        if updated_by:
            self.provenance["updated_by"] = updated_by
        self._refresh_schema_org()
        return self

    def _refresh_schema_org(self) -> None:
        explicit = dict(self.schema_org) if isinstance(self.schema_org, dict) else {}
        self.schema_org = {**schema_org_metadata(self.dtype, self.id), **explicit}

    def __post_init__(self) -> None:
        self.schema_version = STARINTEL_DOC_VERSION
        self.version = max(1, int(self.version or 1))
        self.set_type()
        self.set_id()
        self.timestamp()
        self._refresh_schema_org()

    def asdict(self) -> dict[str, Any]:
        return self.to_dict()

    def to_dict(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        del args, kwargs
        self._refresh_schema_org()
        raw = asdict(self)
        document_id = raw.pop("id")
        revision = raw.pop("rev")
        subtype_data = raw.pop("data") or {}

        common_names = {
            "dataset", "dtype", "schema_version", "version", "date_added", "date_updated",
            "title", "summary", "description", "status", "language", "tags", "labels",
            "aliases", "keywords", "identifiers", "sources", "evidence", "temporal",
            "provenance", "assessment", "verification", "handling", "lineage", "quality",
            "workflow", "geospatial", "attachments", "related_ids", "notes", "schema_org",
            "extensions",
        }
        envelope = {name: raw.pop(name) for name in tuple(common_names)}
        subtype_data.update(raw)

        value: dict[str, Any] = {
            "_id": document_id,
            **envelope,
            "sources": _source_values(envelope["sources"]),
            "data": subtype_data,
        }
        if revision:
            value["_rev"] = revision
        return value

    def to_json(self, *, pretty: bool = False, **kwargs: Any) -> str:
        kwargs.setdefault("ensure_ascii", False)
        kwargs.setdefault("sort_keys", True)
        if pretty:
            kwargs.setdefault("indent", 2)
        else:
            kwargs.setdefault("separators", (",", ":"))
        return json.dumps(self.to_dict(), **kwargs)

    def to_schema_org(self) -> dict[str, Any]:
        return to_schema_org(self.to_dict())

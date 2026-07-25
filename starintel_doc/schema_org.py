#!/usr/bin/env python3
from __future__ import annotations

from copy import deepcopy
from typing import Any

SCHEMA_ORG_CONTEXT = "https://schema.org/"

CANONICAL_DTYPES = (
    "actor-manifest", "address", "alert", "analysis", "asset", "breach",
    "campaign-finance", "claim", "concept", "contract", "dataset-manifest",
    "document", "domain", "education", "email", "email-message", "employment",
    "entity", "event", "evidence-record", "file", "financial-observation", "geo",
    "grant", "host", "investigation-target", "legal-case", "lobbying-filing",
    "location", "media", "meeting", "message", "network", "observation", "org",
    "ownership", "person", "phone", "policy", "procurement", "product", "relation",
    "research-pass", "social-media-post", "source", "target", "task", "url", "user",
)

DTYPE_ALIASES = {
    **{dtype: dtype for dtype in CANONICAL_DTYPES},
    **{dtype.replace("-", "_"): dtype for dtype in CANONICAL_DTYPES},
    "organization": "org",
    "organisation": "org",
    "geolocation": "geo",
    "geographic_location": "geo",
    "email_address": "email",
    "electronic_mail": "email",
    "emailmessage": "email-message",
    "hostname": "host",
    "phone_number": "phone",
    "telephone": "phone",
    "telephone_number": "phone",
    "uniform_resource_locator": "url",
    "web_url": "url",
    "socialmpost": "social-media-post",
    "socialmediapost": "social-media-post",
    "investigationtarget": "investigation-target",
    "researchpass": "research-pass",
    "datasetmanifest": "dataset-manifest",
    "actormanifest": "actor-manifest",
    "legalcase": "legal-case",
    "lobbyingfiling": "lobbying-filing",
    "campaignfinance": "campaign-finance",
    "financialobservation": "financial-observation",
    "evidencerecord": "evidence-record",
}

DTYPE_SCHEMA_ORG_TYPES: dict[str, tuple[str, ...]] = {
    "actor-manifest": ("CreativeWork",),
    "address": ("PostalAddress",),
    "alert": ("SpecialAnnouncement",),
    "analysis": ("CreativeWork",),
    "asset": ("Thing",),
    "breach": ("Event",),
    "campaign-finance": ("CreativeWork",),
    "claim": ("Claim",),
    "concept": ("DefinedTerm",),
    "contract": ("DigitalDocument",),
    "dataset-manifest": ("Dataset",),
    "document": ("CreativeWork",),
    "domain": ("WebSite",),
    "education": ("EducationalOccupationalCredential",),
    "email": ("ContactPoint",),
    "email-message": ("Message",),
    "employment": ("OrganizationRole",),
    "entity": ("Thing",),
    "event": ("Event",),
    "evidence-record": ("CreativeWork",),
    "file": ("DigitalDocument",),
    "financial-observation": ("CreativeWork",),
    "geo": ("GeoCoordinates",),
    "grant": ("Grant",),
    "host": ("Thing",),
    "investigation-target": ("Thing",),
    "legal-case": ("CreativeWork",),
    "lobbying-filing": ("DigitalDocument",),
    "location": ("Place",),
    "media": ("MediaObject",),
    "meeting": ("Event",),
    "message": ("Message",),
    "network": ("Thing",),
    "observation": ("CreativeWork",),
    "org": ("Organization",),
    "ownership": ("Role",),
    "person": ("Person",),
    "phone": ("ContactPoint",),
    "policy": ("CreativeWork",),
    "procurement": ("DigitalDocument",),
    "product": ("Product",),
    "relation": ("Role",),
    "research-pass": ("CreativeWork",),
    "social-media-post": ("SocialMediaPosting",),
    "source": ("CreativeWork",),
    "target": ("Thing",),
    "task": ("Action",),
    "url": ("WebPage",),
    "user": ("Person",),
}


def canonical_dtype(dtype: str) -> str:
    key = str(dtype or "document").strip().lower().replace(" ", "_").replace("-", "_")
    return DTYPE_ALIASES.get(key, DTYPE_ALIASES.get(key.replace("_", "-"), key.replace("_", "-")))


def schema_org_types(dtype: str) -> tuple[str, ...]:
    return DTYPE_SCHEMA_ORG_TYPES.get(canonical_dtype(dtype), ("Thing",))


def schema_org_metadata(dtype: str, document_id: str = "") -> dict[str, Any]:
    canonical = canonical_dtype(dtype)
    types = schema_org_types(canonical)
    value: dict[str, Any] = {
        "@context": SCHEMA_ORG_CONTEXT,
        "@type": types[0] if len(types) == 1 else list(types),
        "additionalType": f"https://starintel.dev/dtype/{canonical}",
    }
    if document_id:
        value["@id"] = document_id
    return value


def to_schema_org(document: dict[str, Any]) -> dict[str, Any]:
    dtype = canonical_dtype(str(document.get("dtype") or "document"))
    data = document.get("data") if isinstance(document.get("data"), dict) else {}
    explicit = document.get("schema_org") if isinstance(document.get("schema_org"), dict) else {}
    value = schema_org_metadata(dtype, str(document.get("_id") or ""))

    name = document.get("title")
    if not name:
        for key in ("display_name", "full_name", "legal_name", "name", "claim", "term", "target"):
            candidate = data.get(key)
            if isinstance(candidate, str) and candidate:
                name = candidate
                break
    value["name"] = str(name or document.get("_id") or "StarIntel record")

    description = document.get("description") or document.get("summary") or data.get("description")
    if description:
        value["description"] = str(description)
    if document.get("aliases"):
        value["alternateName"] = [str(item) for item in document["aliases"]]
    keywords = [str(item) for item in [*document.get("keywords", []), *document.get("tags", [])] if str(item)]
    if keywords:
        value["keywords"] = list(dict.fromkeys(keywords))
    if document.get("language"):
        value["inLanguage"] = str(document["language"])
    if document.get("date_added"):
        value["dateCreated"] = str(document["date_added"])
    if document.get("date_updated"):
        value["dateModified"] = str(document["date_updated"])

    identifiers = []
    for identifier in document.get("identifiers", []):
        if not isinstance(identifier, dict) or identifier.get("value") in (None, ""):
            continue
        item = {
            "@type": "PropertyValue",
            "propertyID": str(identifier.get("scheme") or identifier.get("issuer") or "identifier"),
            "value": identifier["value"],
        }
        if identifier.get("url"):
            item["url"] = str(identifier["url"])
        identifiers.append(item)
    if identifiers:
        value["identifier"] = identifiers

    url = data.get("url") or data.get("website") or data.get("uri")
    if url:
        value["url"] = str(url)
    image = data.get("image_url") or data.get("logo_url")
    if image:
        value["image"] = str(image)
    if document.get("related_ids"):
        value["about"] = [{"@id": str(item)} for item in document["related_ids"]]

    geospatial = document.get("geospatial") if isinstance(document.get("geospatial"), dict) else {}
    if geospatial.get("lat") is not None and (geospatial.get("lon") is not None or geospatial.get("long") is not None):
        value["geo"] = {
            "@type": "GeoCoordinates",
            "latitude": geospatial["lat"],
            "longitude": geospatial.get("lon", geospatial.get("long")),
        }

    value.update(deepcopy(explicit))
    return value


if set(DTYPE_SCHEMA_ORG_TYPES) != set(CANONICAL_DTYPES):
    raise RuntimeError("Schema.org dtype map does not cover the canonical v0.9 dtype set")

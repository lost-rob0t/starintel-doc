#!/usr/bin/env python3
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json, LetterCase
from starintel_doc.documents import Document


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class Domain(Document):
    record_type: str = field(kw_only=True)
    record: str = field(kw_only=True)
    resolved_addresses: list[str] = field(kw_only=True, default_factory=list)

    def set_id(self):
        self.hash_id(self.record, self.record_type)


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class Service:
    port: int = field(kw_only=True)
    name: str = field(kw_only=True)
    version: str = field(kw_only=True, default="")


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class Network(Document):
    org: str = field(kw_only=True, default="")
    asn: int = field(kw_only=True)
    subnet: str = field(kw_only=True)

    def set_id(self):
        self.hash_id(self.org, self.asn.number, self.subnet)


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class Host(Document):
    hostname: str = field(kw_only=True)
    ip: str = field(kw_only=True)
    ports: list[Service] = field(kw_only=True, default_factory=list)
    os: str = field(kw_only=True, default="")

    def set_id(self):
        self.hash_id(self.ip)


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class Url(Document):
    url: str = field(kw_only=True)
    path: str = field(kw_only=True, default="")
    content: str = field(kw_only=True, default="")
    query: str = field(kw_only=True, default="")
    
    def set_id(self):
        self.hash_id(self.url, self.content)


def new_domain(dataset, **kwargs):
    domain = Domain(**kwargs)
    domain.set_meta(dataset)
    return domain


def new_network(dataset, **kwargs):
    network = Network(**kwargs)
    network.set_meta(dataset)
    return network


def new_host(dataset, **kwargs):
    host = Host(**kwargs)
    host.set_meta(dataset)
    return host


def new_url(dataset, **kwargs):
    url = Url(**kwargs)
    url.set_meta(dataset)
    return url

#!/usr/bin/env python3

from dataclasses import dataclass, field
from dataclasses_json import dataclass_json, LetterCase
from starintel_doc.documents import Document


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class Geo(Document):
    lat: float = field(kw_only=True, default=0.0)
    long: float = field(kw_only=True, default=0.0)
    alt: float = field(kw_only=True, default=0.0)

    def set_id(self):
        self.hash_id(self.lat, self.long, self.alt)


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class Address(Geo):
    city: str = field(kw_only=True)
    state: str = field(kw_only=True)
    postal: str = field(kw_only=True)
    country: str = field(kw_only=True)
    street: str = field(kw_only=True)
    street2: str = field(kw_only=True, default="")

    def set_id(self):
        self.hash_id(
            self.lat,
            self.long,
            self.alt,
            self.city,
            self.state,
            self.postal,
            self.country,
            self.street,
            self.street2,
        )


def new_geo(dataset, **kwargs):
    geo = Geo(**kwargs)
    geo.set_meta(dataset)
    return geo


def new_address(dataset, **kwargs):
    address = Address(**kwargs)
    address.set_meta(dataset)
    return address

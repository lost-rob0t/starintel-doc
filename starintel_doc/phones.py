#!/usr/bin/env python3
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json, LetterCase
from starintel_doc.documents import Document


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class Phone(Document):
    number: str = field(kw_only=True)
    carrier: str = field(kw_only=True, default="")
    status: str = field(kw_only=True, default="")
    phone_type: str = field(kw_only=True, default="")

    def set_id(self):
        self.hash_id(self.number)

    def __post_init__(self):
        super().__post_init__()


def new_phone(dataset, **kwargs):
    phone = Phone(**kwargs)
    phone.set_meta(dataset)
    return phone

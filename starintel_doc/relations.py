#!/usr/bin/env python3
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json, LetterCase
from starintel_doc.documents import Document


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class Relation(Document):
    source: str = field(kw_only=True, default="")
    target: str = field(kw_only=True, default="")
    note: str = field(kw_only=True, default="")

    def set_id(self):
        self.ulid_id()


def new_relation(dataset, source, target, note):
    relation = Relation(dataset=dataset, source=source, target=target, note=note)
    relation.set_meta(dataset)
    return relation

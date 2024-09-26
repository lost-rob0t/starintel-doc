#!/usr/bin/env python3
import json
from dataclasses_json import dataclass_json, LetterCase, config
from dataclasses import dataclass, field, asdict
from hashlib import md5
import time
import ulid

STARINTEL_DOC_VERSION = "0.7.3"


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class Document:
    """Meta Class for documents to be stored in starintel."""

    id: str = field(kw_only=True, default="", metadata=config(field_name="_id"))
    dtype: str = field(kw_only=True, default="")
    sources: list[str] = field(default_factory=list, kw_only=True)
    version: str = field(kw_only=True, default=STARINTEL_DOC_VERSION)
    dataset: str = field(default="star-intel", kw_only=True)
    date_added: int = field(default=int(time.time()), kw_only=True)
    date_updated: int = field(default=int(time.time()), kw_only=True)

    @classmethod
    def ulid_id(self):
        self.id = str(ulid.new())

    @classmethod
    def timestamp(self):
        if not self.dateAdded:
            self.dateAdded = int(time.time())
        if not self.dateUpdated:
            self.dateUpdated = int(time.time())

    @classmethod
    def update_timestamp(self):
        self.dateUpdated = int(time.time())

    @classmethod
    def set_id(self):
        if not self.id:
            self.ulid_id()

    @classmethod
    def set_type(self):
        self.dtype = self.__class__.__name__.lower()

    def set_meta(self, dataset):
        self.dataset = dataset
        self.set_type()
        if not self.id or len(self.id) == 0:
            self.set_id()

    def hash_id(self, *data):
        hash_input = "".join(map(str, data))
        self.id = md5(hash_input.encode("utf-8")).hexdigest()

    def __post_init__(self):
        self.set_type()

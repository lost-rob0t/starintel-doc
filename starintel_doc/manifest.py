#!/usr/bin/env python3
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json, LetterCase, config
from hashlib import md5
import time
import ulid


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class ActorManifest:
    """Actor manifest object which advertises actor services."""

    id: str = field(kw_only=True, default="", metadata=config(field_name="_id"))
    rev: str = field(kw_only=True, default="", metadata=config(field_name="_rev"))
    type: str = field(kw_only=True, default="actor-manifest")
    actor: str = field(kw_only=True, default="")
    consumer_path: str = field(kw_only=True, default="")
    target_options: list = field(kw_only=True, default_factory=list)
    date_added: int = field(default_factory=lambda: int(time.time()), kw_only=True)
    date_updated: int = field(default_factory=lambda: int(time.time()), kw_only=True)

    def ulid_id(self):
        self.id = str(ulid.new())

    def timestamp(self):
        if not self.date_added:
            self.date_added = int(time.time())
        if not self.date_updated:
            self.date_updated = int(time.time())

    def update_timestamp(self):
        self.date_updated = int(time.time())

    def hash_id(self, *data):
        hash_input = "".join(map(str, data))
        self.id = md5(hash_input.encode("utf-8")).hexdigest()

    def set_id(self):
        if not self.id or len(self.id) == 0:
            self.hash_id(self.actor)

    def set_type(self):
        self.type = self.__class__.__name__.lower()

    def set_meta(self, dataset):
        self.set_type()
        if not self.id or len(self.id) == 0:
            self.set_id()
        return self

    def __post_init__(self):
        self.set_type()


def new_actor_manifest(actor, **kwargs):
    manifest = ActorManifest(actor=actor, **kwargs)
    return manifest

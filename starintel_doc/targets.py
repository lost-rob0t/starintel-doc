#!/usr/bin/env python3

from dataclasses import dataclass, field
from starintel_doc.documents import Document
from dataclasses_json import dataclass_json, LetterCase


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class Target(Document):
    actor: str = field(kw_only=True)
    target: str = field(kw_only=True)
    delay: int = field(kw_only=True, default=0)
    recurring: bool = field(kw_only=True, default=False)
    options: list = field(kw_only=True, default_factory=list)

    def set_id(self):
        self.hash_id(self.dataset, self.target, self.actor)

    def __post_init__(self):
        super().__post_init__()


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class Scope:
    description: str
    outscope: list = field(default_factory=list)
    inscope: list = field(default_factory=list)
    scope_type: str = field(default="domain")

    def __post_init__(self):
        super().__post_init__()


def scope_add_to_options(target, scope):
    target.options.append(scope)


def add_inscope(scope, thing):
    scope.inscope.append(thing)


def new_target(dataset, target, actor, options=None, delay=0, recurring=False):
    if options is None:
        options = []
    target_instance = Target(
        actor=actor, target=target, delay=delay, recurring=recurring, options=options
    )
    target_instance.set_meta(dataset)
    return target_instance

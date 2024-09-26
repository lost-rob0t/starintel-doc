#!/usr/bin/env python3

from dataclasses_json import dataclass_json, LetterCase
from dataclasses import dataclass, field
from starintel_doc.documents import Document


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class Entity(Document):
    "A object Representing a entity"
    etype: str = field(kw_only=True, default="")
    eid: str = field(kw_only=True, default="")

    def __post_init__(self):
        super().__post_init__()


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class Person(Entity):
    """
    Person class.
    """

    # pylint: disable=too-many-instance-attributes

    fname: str = field(kw_only=True, default="")
    lname: str = field(kw_only=True, default="")
    mname: str = field(default="", kw_only=True)
    gender: str = field(default="", kw_only=True)
    bio: str = field(default="", kw_only=True)
    dob: str = field(default="", kw_only=True)
    race: str = field(default="", kw_only=True)
    misc: list[str] = field(default_factory=list, kw_only=True)

    def set_id(self):
        self.ulid_id()

    def __post_init__(self):
        super().__post_init__()


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class Org(Entity):
    """Organization class. You should use this for NGO, governmental agencies and corpations."""

    name: str = field(kw_only=True, default="")
    website: str = field(kw_only=True, default="")
    country: str = field(default="")
    bio: str = field(default="")
    reg: str = field(kw_only=True, default="")

    def __post_init__(self):
        super().__post_init__()

    def set_id(self):
        # Set the ID for an Org document using a hash of its name, reg, and country
        self.hash_id(self.name, self.reg, self.country)


def new_org(dataset, name, etype, **kwargs):
    # Create a new Org instance and set its metadata
    org = Org(name=name, etype=etype, **kwargs)
    org.set_meta(dataset)
    return org


def new_person(dataset, fname, lname, etype, **kwargs):
    # Create a new Person instance and set its metadata
    person = Person(fname=fname, lname=lname, etype=etype, **kwargs)
    person.set_meta(dataset)
    return person

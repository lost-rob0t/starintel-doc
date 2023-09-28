import json
from dataclasses import dataclass, field, asdict
from hashlib import sha256
import time


def make_id(json: str) -> str:
    return sha256(bytes(json, encoding="utf-8")).hexdigest()

@dataclass
class Document():
    """Meta Class for documents to be stored in starintel.
    If the Document is labeled private then
    the meta data will be labeled private and will
    not be gloably searched."""

    id: str = field(kw_only=True, default="")
    dtype: str = field(kw_only=True, default="")
    dataset: str = field(default="Star Intel", kw_only=True)
    dateAdded: int = field(default=int(time.time()), kw_only=True)
    dateUpdated: int = field(default=int(time.time()), kw_only=True)

    @property
    def __dict__(self):
        data = asdict(self)
        # For compat with nim
        data["_id"] = data.pop("id")
        return data
    @property
    def json(self):
        return json.dumps(self.__dict__)
    def __post_init__(self):
        # Set the type of object based on the class name
        self.dtype = self.__class__.__name__

    @classmethod
    def from_json(cls, json_str):
        data = json.loads(json_str)
        if "_id" in data:
            data["id"] = data.pop("_id")

        return cls(**data)

@dataclass
class Entity(Document):
    etype: str = field(kw_only=True, default="")
    eid: str = field(kw_only=True, default="")


@dataclass
class Person(Entity):
    """
    Person class.
    """
    fname: str = field(kw_only=True, default="")
    lname: str = field(kw_only=True, default="")
    mname: str = field(default="", kw_only=True)
    gender: str = field(default="", kw_only=True)
    bio: str = field(default="", kw_only=True)
    dob: str = field(default="", kw_only=True)
    socialMedia: list[dict] = field(default_factory=list, kw_only=True)
    phones: list[dict] = field(default_factory=list, kw_only=True)
    address: list[dict] = field(default_factory=list, kw_only=True)
    emails: list[dict] = field(default_factory=list, kw_only=True)
    orgs: list[dict] = field(default_factory=list, kw_only=True)
    misc: list[str] = field(default_factory=list, kw_only=True)

@dataclass
class Org(Document):
    """Organization class. You should use this for NGO, governmental agencies and corpations."""

    name: str = field(kw_only=True, default="")
    website: str = field(kw_only=True, default = "")
    country: str = field(default="")
    bio: str = field(default="")
    orgtype: str = field(kw_only=True, default="NGO")
    reg: str = field(kw_only=True, default="")
    members: list[dict] = field(default_factory=list)
    address: list[dict] = field(default_factory=list)

@dataclass
class Email(Document):
    """Email class. This class also serves as a psuedo email:pass combo"""
    user: str = field(kw_only=True, default="")
    domain: str = field(kw_only=True, default="")
    password: str = field(kw_only=True, default="")
    dataBreach: list[str] = field(default_factory=list, kw_only=True)

@dataclass
class CVE(Document):
    cveNumber: str
    score: int

@dataclass
class Mesaage(Document):
    """Class For a instant message. This is best suited for Discord/telegram like chat services."""
    platform: str  # Domain of platform aka telegram.org. discord.gg
    media: list[str] = field(kw_only=True, default_factory=list)
    user: str = field(kw_only=True)
    # Should be a hash of groupname, message, date and user.
    # Using this system we can track message replys across platforms amd keeps it easy
    messageId: str = field(kw_only=True)
    group: str = field(kw_only=True)  # Server name if discord
    channelName: str = field(kw_only=True, default="")  # only used incase like discord
    message: str = field(kw_only=True)
    isReply: bool = field(kw_only=True, default=False)
    replyTo: dict = field(kw_only=True, default_factory=dict)

@dataclass
class Geo:
    lat: float = field(kw_only=True, default=0.0)
    long: float = field(kw_only=True, default=0.0)
    gid: str = field(kw_only=True, default="")

@dataclass
class Address(Geo):
    """Class for an Adress. Currently only for US addresses but may work with others."""
    street: str = field(kw_only=True, default="")
    city: str = field(kw_only=True, default="")
    state: str = field(kw_only=True, default="")
    street2: str = field(kw_only=True, default="")
    postal: str = field(kw_only=True, default="")
    country: str = field(kw_only=True, default="")

@dataclass
class User(Document):
    """Class for Online user. has no specifics use to represent a online prescense."""
    name: str
    platform: str
    email: list[str] = field(kw_only=True, default_factory=list)
    phones: list[str] = field(kw_only=True, default_factory=list)
    misc: list[dict] = field(kw_only=True, default_factory=list)

@dataclass
class Phone(Document):
    """Class for phone numbers."""
    number: str = field(kw_only=True, default="")
    carrier: str = field(kw_only=True, default="")
    status: str = field(kw_only=True, default="")
    phoneType: str = field(kw_only=True, default="")

@dataclass
class SocialMPost(Document):
    """class for Social media posts from places such as reddit or mastodon/twitter"""
    content: str = field(kw_only=True)
    url: str = field(kw_only=True)
    user: dict = field(kw_only=True)
    replies: list[dict] = field(kw_only=True, default_factory=list)
    media: list[str] = field(kw_only=True, default_factory=list)
    links: list[str] = field(kw_only=True, default_factory=list)
    tags: list[str] = field(kw_only=True, default_factory=list)
    replyCount: int = field(kw_only=True, default=0)
    repostCount: int = field(kw_only=True, default=0)
    group: str = field(kw_only=True)

@dataclass
class Relation(Document):
    relation: str = field(kw_only=True)
    source: str = field(kw_only=True)
    target: str = field(kw_only=True)
    notes: str = field(kw_only=True)



@dataclass
class Target:
    """Automation object, holds configution for actors (bots) to preform tasks"""
    id: str = field(kw_only=True, default = "")
    actor: str = field(kw_only=True, default = "")
    target: str = field(kw_only=True, default = "")
    dataset: str = field(kw_only=True, default = "")
    options: dict = field(kw_only=True, default_factory = dict)

    @property
    def __dict__(self):
        data = asdict(self)
        # For compat with nim
        #
        data["_id"] = data["id"]
        data.pop("id")
        return data
    @property
    def json(self):
        return json.dumps(self.__dict__)
    def __post_init__(self):
        # Set the type of object based on the class name
        self.dtype = self.__class__.__name__


@dataclass
class Web(Document):
    source: str = field(kw_only=True, default = "")

@dataclass
class Domain(Web):
    recordType: str = field(kw_only=True, default= "")
    record: str = field(kw_only=True)
    ip: str = field(kw_only=True)


@dataclass
class Port:
    number: int = field(kw_only=True)
    services: list[str] = field(kw_only=True, default_factory=list)
    @property
    def __dict__(self):
        return asdict(self)
    @property
    def json(self):
        return json.dumps(self.__dict__)


@dataclass
class ASN:
    number: int = field(kw_only=True)
    subnet: str = field(kw_only=True)
    @property
    def __dict__(self):
        return asdict(self)
    @property
    def json(self):
        return json.dumps(self.__dict__)

@dataclass
class Network:
    org: dict = field(kw_only=True, default_factory=dict)
    asn: dict = field(kw_only=True, default_factory=dict)
    @property
    def __dict__(self):
        return asdict(self)
    @property
    def json(self):
        return json.dumps(self.__dict__)

@dataclass
class Host(Web):
    hostname: str = field(kw_only=True, default = "")
    ip: str = field(kw_only=True)
    os: str = field(kw_only=True, default="")
    ports: list[dict] = field(kw_only=True, default_factory=list)
    network: dict = field(kw_only=True, default_factory=dict)

@dataclass
class Url(Web):
    url: str = field(kw_only=True)
    content: str = field(kw_only=True)

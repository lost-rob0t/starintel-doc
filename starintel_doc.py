import json
import random
import uuid
from dataclasses import dataclass, field, asdict
from hashlib import sha256
from datetime import datetime
import couchdb2
import time
import star_exceptions
__version__ = "0.6.0"


def make_id(json: str) -> str:
    return sha256(bytes(json, encoding="utf-8")).hexdigest()


@dataclass
class BookerDocument:
    """Meta Class for documents to be stored in starintel.
    If the Document is labeled private then
    the meta data will be labeled private and will
    not be gloably searched."""

    _id: str = field(kw_only=True, default=None)
    dtype: str = field(kw_only=True, default="")
    dataset: str = field(default="Star Intel", kw_only=True)
    date_added: int = field(default=int(time.time()), kw_only=True)
    date_updated: int = field(default=int(time.time()), kw_only=True)

    @property
    def __dict__(self):
        return asdict(self)
    @property
    def json(self):
        return json.dumps(self.__dict__)

@dataclass
class BookerEntity(BookerDocument):
    etype: str = field(kw_only=True, default="")
    eid: str = field(kw_only=True, default="")

    @property
    def __dict__(self):
        return asdict(self)
    @property
    def json(self):
        return json.dumps(self.__dict__)


@dataclass
class BookerPerson(BookerEntity):
    """
    Person class.
    """
    fname: str = field(kw_only=True, default="")
    lname: str = field(kw_only=True, default="")
    mname: str = field(default="", kw_only=True)
    gender: str = field(default="", kw_only=True)
    bio: str = field(default="", kw_only=True)
    dob: str = field(default="", kw_only=True)
    social_media: list[dict] = field(default_factory=list, kw_only=True)
    phones: list[dict] = field(default_factory=list, kw_only=True)
    address: list[dict] = field(default_factory=dict, kw_only=True)
    emails: list[dict] = field(default_factory=list, kw_only=True)
    orgs: list[dict] = field(default_factory=list, kw_only=True)
    dtype = "person"
    misc: list[str] = field(default_factory=list, kw_only=True)

@dataclass
class BookerOrg(BookerDocument):
    """Organization class. You should use this for NGO, governmental agencies and corpations."""

    name: str = field(kw_only=True, default="")

    country: str = field(default="")
    bio: str = field(default="")
    orgtype: str = field(kw_only=True, default="NGO")
    reg: str = field(kw_only=True, default="")
    members: list[dict] = field(default_factory=list)
    address: list[dict] = field(default_factory=list)
    dtype = "org"

@dataclass
class BookerEmail(BookerDocument):
    """Email class. This class also serves as a psuedo email:pass combo"""
    email_username: str = field(kw_only=True, default="")
    email_domain: str = field(kw_only=True, default="")
    email_password: str = field(kw_only=True, default="")
    data_breach: list[str] = field(default_factory=list, kw_only=True)
    dtype = "email"

@dataclass
class BookerBreach(BookerDocument):
    date: str
    total: int
    description: str
    url: str
    dtype = "breach"
@dataclass
class BookerWebService(BookerDocument):
    port: int
    service_name: str
    service_version: str
    source: str
    ip: str
    owner: str
    dtype = "service"

@dataclass
class BookerHost(BookerDocument):
    ip: str
    hostname: str
    operating_system: str
    date: str
    asn: int = field(kw_only=True, default=0)
    country: str = field(kw_only=True, default="")
    network_name: str = field(kw_only=True, default="")
    owner: str = field(kw_only=True, default="")
    vulns: list[dict] = field(default_factory=list)
    services: list[dict] = field(default_factory=list)
    dtype = "host"

@dataclass
class BookerCVE(BookerDocument):
    cve_number: str
    score: int
    dtype = "cve"
@dataclass
class BookerMesaage(BookerDocument):
    """Class For a instant message. This is best suited for Discord/telegram like chat services."""
    platform: str  # Domain of platform aka telegram.org. discord.gg
    media: list[str] = field(kw_only=True, default_factory=list)
    username: str = field(kw_only=True)
    # Should be a hash of groupname, message, date and username.
    # Using this system we can track message replys across platforms amd keeps it easy
    message_id: str = field(kw_only=True)
    group: str = field(kw_only=True)  # Server name if discord
    channel_name: str = field(kw_only=True, default="")  # only used incase like discord
    message: str = field(kw_only=True)
    isReply: bool = field(kw_only=True, default=False)
    replyTo: dict = field(kw_only=True, default_factory=dict)
    dtype = "message"

@dataclass
class BookerGeo:
    lat: float = field(kw_only=True, default=0.0)
    long: float = field(kw_only=True, default=0.0)
    gid: str = field(kw_only=True, default="")

@dataclass
class BookerAddress(BookerGeo):
    """Class for an Adress. Currently only for US addresses but may work with others."""
    street: str = field(kw_only=True, default="")
    city: str = field(kw_only=True, default="")
    state: str = field(kw_only=True, default="")
    street2: str = field(kw_only=True, default="")
    postal: str = field(kw_only=True, default="")
    country: str = field(kw_only=True, default="")
    dtype = "address"

@dataclass
class BookerUsername(BookerDocument):
    """Class for Online username. has no specifics use to represent a online prescense."""
    username: str
    platform: str
    email: list[str] = field(kw_only=True, default_factory=list)
    phones: list[str] = field(kw_only=True, default_factory=list)
    misc: list[dict] = field(kw_only=True, default_factory=list)
    dtype = "username"

@dataclass
class BookerPhone(BookerDocument):
    """Class for phone numbers."""
    phone: str = field(kw_only=True, default="")
    carrier: str = field(kw_only=True, default="")
    status: str = field(kw_only=True, default="")
    phone_type: str = field(kw_only=True, default="")
    dtype = "phone"

@dataclass
class BookerSocialMPost(BookerDocument):
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
class BookerTarget:
    """Automation object, holds configution for actors (bots) to preform tasks"""
    _id: str field(kw_only=True, default = "")
    actor: str field(kw_only=True, default = "")
    target: str field(kw_only=True, default = "")
    dataset: str field(kw_only=True, default = "")
    options: dict field(kw_only=True, default_factory = dict)

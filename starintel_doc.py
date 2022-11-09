import json
import random
import uuid
from dataclasses import dataclass, field, asdict
from hashlib import sha256
from datetime import datetime
import couchdb2
import star_exceptions
__version__ = "0.5.0"


def make_id(json: str) -> str:
    return sha256(bytes(json, encoding="utf-8")).hexdigest()


@dataclass
class BookerDocument:
    """Meta Class for documents to be stored in starintel.
    If the Document is labeled private then
    the meta data will be labeled private and will
    not be gloably searched."""

    is_public: bool = field(kw_only=True, init=True, default=True)
    operation_id: int = field(kw_only=True, init=True, default=0)
    _id: str = field(kw_only=True, default=None)
    _rev: str = field(kw_only=True, default=None)
    _attachments: dict = field(default_factory=dict, kw_only=True)
    dtype: str = field(kw_only=True, default="")
    source_dataset: str = field(default="Star Intel", kw_only=True)
    dataset: str = field(default="Star Intel", kw_only=True)
    date_added: str = field(default=datetime.now().isoformat(), kw_only=True)
    date_updated: str = field(default=datetime.now().isoformat(), kw_only=True)

    @property
    def __dict__(self):
        return asdict(self)
    @property
    def json(self):
        return json.dumps(self.__dict__)

@dataclass
class BookerEntity:
    etype: str = field(kw_only=True, default="")
    eid: str = field(kw_only=True, default="")

    @property
    def __dict__(self):
        return asdict(self)
    @property
    def json(self):
        return dumps(self.__dict__)


@dataclass
class BookerPerson(BookerDocument):
    """Person class.
       WARNING: When creating a person document, make sure to only place document id
       if you do not the resolve method will be useless and whats the point of metadata?""
    """
    fname: str = field(kw_only=True, default="")
    lname: str = field(kw_only=True, default="")
    mname: str = field(default="", kw_only=True)
    gender: str = field(default="", kw_only=True)
    political_party: str = field(default="", kw_only=True)
    bio: str = field(default="", kw_only=True)
    age: int = field(default=0, kw_only=True)
    dob: str = field(default="", kw_only=True)
    social_media: list[str] = field(default_factory=list, kw_only=True)
    phones: list[str] = field(default_factory=list, kw_only=True)
    address: list[str] = field(default_factory=list, kw_only=True)
    ip: list[str] = field(default_factory=list, kw_only=True)
    data_breach: list[str] = field(default_factory=list, kw_only=True)
    emails: list[str] = field(default_factory=list, kw_only=True)
    organizations: list[str] = field(default_factory=list, kw_only=True)
    memberships: list[str] = field(default_factory=list, kw_only=True)
    education: list[dict] = field(default_factory=list, kw_only=True)
    comments: list[dict] = field(default_factory=list, kw_only=True)
    type = "person"

    def resolve(self, client):
        """For each remote document load and build a BookerDocument.
           This function returns BookerDocuments for each of the different arrays.
           """
        resolved_emails = []
        resolved_phones = []
        resolved_orgs = []
        resolved_social_media = []
        resolved_ip = []
        resolved_memberships = []
        ids = []
        ids = ids.extend(self.organizations)
        ids = ids.extend(self.emails)
        ids = ids.extend(self.address)
        ids = ids.extend(self.phones)
        ids = ids.extend(self.ip)
        ids = ids.extend(self.social_media)
        ids = ids.extend(self.memberships)
        docs = client.get_bulk(ids)

        for doc_ in docs:
            if doc_ is not None:
                try:
                    dtype = doc_['type']
                    if dtype == "email":
                        resolved_emails.append(BookerEmail().load(doc_))
                    elif dtype == "org":
                        resolved_orgs.append(BookerOganizations().load(doc_))
                    elif dtype == "phone":
                        resolved_phones.append(BookerPhone().load(doc_))
                    elif dtype == "username":
                        resolved_social_media.append(BookerUsername().load(doc_))
                    elif dtype == "membership":
                        resolved_memberships.append(BookerMembership().load(doc_))
                except KeyError:
                    raise star_exceptions.TypeMissingError()

@dataclass
class BookerOganizations(BookerDocument):
    """Organization class. You should use this for NGO, governmental agencies and corpations."""

    name: str = field(kw_only=True, default="")

    country: str = field(default="")
    bio: str = field(default="")
    organization_type: str = field(kw_only=True, default="NGO")
    reg_number: str = field(kw_only=True, default="")
    members: list[dict] = field(default_factory=list)
    address: list[dict] = field(default_factory=list)
    email_formats: list[str] = field(default_factory=list)
    type = "org"

    def make_doc(self, use_json=False):
        """Build a document. To generate a json document set `use_json` to `True`"""
        metadata = {
            "name": self.name,
            "country": self.country,
            "members": self.members,
            "address": self.address,
            "reg_number": self.reg_number,
            "org_type": self.organization_type,
            "email_formats": self.email_formats,
        }
        if self.is_public:
            doc = {
                "operation_id": self.operation_id,
                "type": "org",
                "date_added": self.date_added,
                "date_updated": self.date_updated,
                "dataset": self.dataset,
                "source_dataset": self.source_dataset,
                "metadata": metadata,
                "owner_id": self.owner_id
            }
        else:
            doc = {
                "operation_id": self.operation_id,
                "type": "org",
                "date_added": self.date_added,
                "date_updated": self.date_updated,
                "dataset": self.dataset,
                "source_dataset": self.source_dataset,
                "private_metadata": metadata,
                "owner_id": self.owner_id
            }
        if use_json:
            return json.dumps(doc)
        else:
            return doc

@dataclass
class BookerEmail(BookerDocument):
    """Email class. This class also serves as a psuedo email:pass combo"""
    owner: str = field(kw_only=True)
    email_username: str = field(kw_only=True, default="")
    email_domain: str = field(kw_only=True, default="")
    email_password: str = field(kw_only=True, default="")
    data_breach: list[str] = field(default_factory=list, kw_only=True)
    username: dict = field(kw_only=True, default_factory=dict)
    type = "email"

    def make_doc(self, use_json=False):
        """Build a document. To generate a json document set `use_json` to `True`"""
        metadata = {
            "owner": self.owner,
            "email_username": self.email_username,
            "username": self.username,
            "email_domain": self.email_domain
        }
        if self.is_public:
            doc = {
                "operation_id": self.operation_id,
                "type": "email",
                "date_added": self.date_added,
                "date_updated": self.date_updated,
                "dataset": self.dataset,
                "source_dataset": self.source_dataset,
                "metadata": metadata,
                "owner_id": self.owner_id
            }
        else:
            doc = {
                "operation_id": self.operation_id,
                "type": "email",
                "date_added": self.date_added,
                "date_updated": self.date_updated,
                "dataset": self.dataset,
                "source_dataset": self.source_dataset,
                "private_metadata": metadata,
                "owner_id": self.owner_id
            }
        if self._id:
            doc["_id"] = self._id
        if self._rev:
            doc["_rev"] = self._rev

        if use_json:
            return json.dumps(doc)
        else:
            return doc

@dataclass
class BookerBreach(BookerDocument):
    date: str
    total: int
    description: str
    url: str
    type = "breach"
@dataclass
class BookerWebService(BookerDocument):
    port: int
    service_name: str
    service_version: str
    source: str
    ip: str
    owner: str
    type = "service"

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
    type = "host"

@dataclass
class BookerCVE(BookerDocument):
    cve_number: str
    score: int
    type = "cve"
@dataclass
class BookerMesaage(BookerDocument):
    """Class For a instant message. This is best suited for Discord/telegram like chat services."""
    platform: str  # Domain of platform aka telegram.org. discord.gg
    media: bool
    username: str = field(kw_only=True)
    fname: str = field(kw_only=True, default="")
    lname: str = field(kw_only=True, default="")
    phone: str = field(kw_only=True, default="")  # Used for signal and telegram
    user_id: str = field(
        kw_only=True, default=""
    )  # Hash the userid of the platform to keep it uniform
    # Should be a hash of groupname, message, date and username.
    # Using this system we can track message replys across platforms amd keeps it easy
    message_id: str = field(kw_only=True)
    group_name: str = field(kw_only=True)  # Server name if discord
    channel_name: str = field(kw_only=True, default="")  # only used incase like discord
    message: str = field(kw_only=True)
    message_type: str = field(kw_only=True)  # type of message
    is_reply: bool = field(kw_only=True, default=False)
    reply_id: str = field(kw_only=True, default="")

    def make_id(self):
        hinput = self.message + self.channel_name + self.group_name + self.date_added + self.username
        self._id = make_id(hinput)
        return self._id

@dataclass
class BookerAddress(BookerDocument):
    """Class for an Adress. Currently only for US addresses but may work with others."""
    street: str = field(kw_only=True, default="")
    city: str = field(kw_only=True, default="")
    state: str = field(kw_only=True, default="")
    apt: str = field(kw_only=True, default="")
    zip: str = field(kw_only=True, default="")
    members: list = field(kw_only=True, default_factory=list)
    type = "address"

@dataclass
class BookerUsername(BookerDocument):
    """Class for Online username. has no specifics use to represent a online prescense."""
    username: str
    platform: str
    owner: str = field(kw_only=True, default="")
    email: str = field(kw_only=True, default="")
    phone: str = field(kw_only=True, default="")
    memberships: list[str] = field(kw_only=True, default_factory=list)
    type = "username"

@dataclass
class BookerPhone(BookerDocument):
    """Class for phone numbers."""
    owner:  str = field(kw_only=True, default="")
    phone: str = field(kw_only=True, default="")
    carrier: str = field(kw_only=True, default="")
    status: str = field(kw_only=True, default="")
    phone_type: str = field(kw_only=True, default="")


@dataclass
class BookerMembership(BookerDocument):
    """Class for tracking a person's membership(s).
        a membership is any relation between BookerOrganizations or BookerPerson
        This Class is still WIP."""
    type = "membership"
    start_date:  str = field(kw_only=True, default="")
    end_date:  str = field(kw_only=True, default="")
    roles: list[str] = field(kw_only=True, default_factory=list)
    title:  str = field(kw_only=True, default="")

def get_meta(doc):
    """Load the documunt metadata field wether it is private or not"""
    meta = doc.get("metadata")
    if meta is None:
        meta = doc.get("private_metadata")

    # if meta is still None the type field is not set.
    if meta is None:
        raise star_exceptions.TypeMissingError()
    else:
        return meta

def load_doc(client, doc):
    """Load a document. it will determin the type then load it."""
    obj = None
    if doc is not None:
        type = doc.get("type")
        if type is None:
            raise star_exceptions.TypeMissingError()
        else:
            if type == "person":
                obj = BookerPerson().load(doc)
            elif type == "org":
                obj = BookerOganizations().load(doc)
            elif type == "email":
                obj = BookerEmail().load(doc)
            elif type == "address":
                obj = BookerAddress().load(doc)
        if obj is None:
            raise star_exceptions.DocumentParseError("Failed to load document becuase a type could not be matched")
        else:
            return obj

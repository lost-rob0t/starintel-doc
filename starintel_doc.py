import json
import random
from dataclasses import dataclass, field
from hashlib import sha256
import secrets
from datetime import datetime
import couchdb2
import star_exceptions
from dataclasses_json import dataclass_json
__version__ = "0.4.7"


def make_id(json: str) -> str:
    return sha256(bytes(json, encoding="utf-8")).hexdigest()

@dataclass_json
@dataclass()
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
    owner_id: int = field(kw_only=True, default=0)
    document_id: str = field(kw_only=True, default="")
    type: str = field(kw_only=True, default="")
    source_dataset: str = field(default="Star Intel", kw_only=True)
    dataset: str = field(default="Star Intel", kw_only=True)
    date_added: str = field(default=datetime.now().isoformat(), kw_only=True)
    date_updated: str = field(default=datetime.now().isoformat(), kw_only=True)
    doc: dict = field(default_factory=dict, kw_only=True)
    memberships: set = field(default_factory=set, kw_only=True)

    def parse_doc(self, doc):
        self.doc = json.loads(doc)
        if self.doc.get("_id", None) is not None:
            self._id = self.doc["_id"]
        if self.doc.get("_rev", None) is not None:
            self._rev = self.doc["_rev"]
        if self.doc.get("_attachments", None) is not None:
            self._attachments = self.doc["_attachments"]

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
                except KeyError:
                    raise star_exceptions.TypeMissingError()

    def make_id(self):
        hinput = self.fname + self.mname + self.lname + self.dob
        self._id = make_id(hinput)
        return self._id


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

    def make_id(self):
        hinput = self.name + self.country
        self._id = make_id(hinput)
        return self._id

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

    def make_resolve(self):
        """Builds a dict for a resolve result"""
        data = {}
        data["email"] = self.email_username + "@" + self.email_domain
        data["password"] = self.email_password
        data["data_breaches"] = []
        for breach in self.data_breach:
            data["data_breaches"].append(breach)
        data["owner"] = self.owner
        return data
    def make_id(self):
        hinput = self.email_username + self.email_domain + self.email_password
        self._id = make_id(hinput)
        return self._id

@dataclass
class BookerBreach(BookerDocument):
    date: str
    total: int
    description: str
    url: str
    type = "breach"

    def load(self, doc):
        """Load a document from json."""
        if doc.get("type") == "breach":
            meta = get_meta(doc)
            self._id = doc.get("_id")
            self._rev = doc.get("_rev")
            self.date_added = doc.get("date_added")
            self.date_updated = doc.get("date_updated")
            self.source_dataset = doc.get("source_dataset")
            self.dataset = doc.get("dataset")
            self.owner_id = doc.get("owner_id")
            self.date = meta.get("date")
            self.total = meta.get("total")
            self.description = meta.get("description")
            self.url = meta.get("url")
        return self

    def make_doc(self):
        hinput = self.url
        self._id = make_id(hinput)
        return self._id

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

    def make_id(self):
        hinput = self.ip + self.hostname
        self._id = make_id(hinput)
        return self._id

@dataclass
class BookerCVE(BookerDocument):
    cve_number: str
    score: int
    type = "cve"

@dataclass
class BookerMessage(BookerDocument):
    """Class For a instant message. This is best suited for Discord/telegram like chat services."""
    platform: str  # Domain of platform aka telegram.org. discord.gg
    media: bool
    username: str = field(kw_only=True)
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

    def make_id(self, unique=True):
        if not unique:
            hinput = self.username + self.platform
            self._id = make_id(hinput)
        else:
            self._id = make_id(secrets.token_hex(16))
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
    fname: str = field(kw_only=True, default="")
    lname: str = field(kw_only=True, default="")
    type = "username"

    def make_id(self, unique=True):
        if not unique:
            hinput = self.username + self.platform
            self._id = make_id(hinput)
        else:
            self._id = make_id(secrets.token_hex(16))
        return self._id
@dataclass
class BookerPhone(BookerDocument):
    """Class for phone numbers."""
    owner:  str = field(kw_only=True, default="")
    phone: str = field(kw_only=True, default="")
    carrier: str = field(kw_only=True, default="")
    status: str = field(kw_only=True, default="")
    phone_type: str = field(kw_only=True, default="")

    def make_id(self):
        self._id = make_id(secrets.token_hex(16))
        return self._id


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
    child:  str = field(kw_only=True, default="")
    parent:  str = field(kw_only=True, default="")
    def make_id(self):
        self._id = make_id(self.title)
        return self._id

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

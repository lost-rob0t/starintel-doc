import json
import random
import uuid
from dataclasses import dataclass, field
from hashlib import sha256
from datetime import datetime
__version__ = "0.1.7"

@dataclass
class BookerDocument:
    """Class for Documents to be stored in Booker
        If the Document is labeled private then 
        the meta data will be labled private and will
        not be gloably searched."""
    is_public: bool
    _id: str = field(kw_only=True, default=None) 
    _rev: str = field(kw_only=True, default=None) 
    owner_id: int = field(kw_only=True, default=0)
    document_id: str = field(kw_only=True, default="")
    object_type: str = field(kw_only=True, default="")
    source_dataset: str = field(default="Star Intel", kw_only=True)
    dataset: str  = field(default="Star Intel", kw_only=True)
    date_added: str = field(default="Star Intel", kw_only=True)

    def make_id(self, json: str) -> str:
        return sha256(bytes(json, encoding="utf-8")).hexdigest()
@dataclass
class BookerPerson(BookerDocument):
    fname: str =field(kw_only=True)
    lname: str = field(kw_only=True)
    mname: str = field(default="", kw_only=True)
    bio: str  = field(default="", kw_only=True)
    age: int = field(default=0, kw_only=True)
    dob: str  = field(default="", kw_only=True)
    social_media: list = field(default_factory=list, kw_only=True)
    phones: list[dict] = field(default_factory=list, kw_only=True)
    address: list[dict] = field(default_factory=list, kw_only=True)
    ip: list[dict] = field(default_factory=list, kw_only=True)
    data_breach: list[dict] = field(default_factory=list, kw_only=True)
    emails:  list[dict] = field(default_factory=list, kw_only=True)
    employment_history:  list[dict] = field(default_factory=list, kw_only=True)
    organizations:  list[dict] = field(default_factory=list, kw_only=True)
    comments:  list[dict] = field(default_factory=list, kw_only=True)
    def make_doc(self, use_json=False):
    
        metadata = {'fname': self.fname, 'mname': self.mname, 
                        'lname': self.lname, 'age': self.age, 
                        'dob': self.dob, 'emails': self.emails, 
                        'phones': self.phones, 'employments': self.employment_history, 
                        'ip': self.ip, 'orgs': self.organizations, 'comments': self.comments,
                        'bio': self.bio, 'locations': self.address}

    
        if self.is_public:
            doc = {'type': "person", 'date': self.date_added, 
                    'source_dataset': self.source_dataset, 
                    'metadata': metadata}
                    
        else:
            doc = {'type': "person", 'date': self.date_added, 

                    'source_dataset': self.source_dataset, 
                    'private_metadata': metadata}
        if self._id:
            doc["_id"] = self._id
        if self._rev:
            doc["_rev"] = self._rev
        if use_json:
            return json.dumps(doc)
        else:
            return doc


@dataclass
class BookerOganizations(BookerDocument):
    name: str
    country: str = field(default="")
    bio: str = field(default="")
    organization_type: str = field(kw_only=True, default="NGO") 
    members:  list[dict] = field(default_factory=list)    
    address:  list[dict] = field(default_factory=list)    
    email_formats:  list[str] = field(default_factory=list)
    def make_doc(self, use_json=False):
        metadata = {'name': self.name, 'country': self.country, 
                    'members': self.members, "address": self.address,
                    'org_type': self.organization_type, 'email_formats': self.email_formats}
        if self.is_public:
            doc = {'type': "org", 'date': self.date_added, 
                    'source_dataset': self.source_dataset, 
                    'metadata': metadata}
        else:
            doc = {'type': "org", 'date': self.date_added, 
                    'source_dataset': self.source_dataset, 
                    'private_metadata': metadata}
        if use_json:
            return json.dumps(doc)
        else:
            return doc


@dataclass
class BookerMember(BookerPerson):
    title: str
    organization: str
    roles: list[str] = field(default_factory=list, kw_only=True)
    start_date: str = field(kw_only=True, default=datetime.now().isoformat())
    end_date: str = field(kw_only=True, default="")

    def make_doc(self, use_json=False):
        self.organizations.append(self.organization)
        metadata = {
                    'roles': self.roles, 
                    'start_date': self.start_date, 
                    'end_date': self.end_date}
        if self.is_public:
            doc = {'type': "member", 'date': self.date_added, 
                    'source_dataset': self.source_dataset, 
                    'metadata': metadata}
        else:
            doc = {'type': "member", 'date': self.date_added,  
                    'source_dataset': self.source_dataset, 
                    'private_metadata': metadata}
        if use_json:
            return json.dumps(doc)
        else:
            return doc

@dataclass
class BookerEmail(BookerDocument):
    owner: str =  field(kw_only=True)
    email_username: str =  field(kw_only=True, default="")
    email_domain: str = field(kw_only=True, default="")
    date_seen: str  = field(kw_only=True, default="")
    data_breach: list[dict] = field(default_factory=list, kw_only=True)
    def make_doc(self, use_json=False):
        metadata = {'owner': self.owner, 'username': self.email_username, 
                    'domain': self.email_domain, 'seen': self.date_seen}
        if self.is_public:
            doc = {'type': "email", 'date': self.date_added,  
                    'source_dataset': self.source_dataset, 
                    'metadata': metadata}
        else:
            doc = {'type': "email", 'date': self.date_added,  
                    'source_dataset': self.source_dataset, 
                    'private_metadata': metadata}
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
    def make_doc(self, use_json=False):
        metadata = {'date': self.date, 'total': self.total, 
                    'description': self.description, 'url': self.url}
        if self.is_public:
            doc = {'type': "breach", 
                    'source_dataset': self.source_dataset, 
                    'metadata': metadata}
        else:
            doc = {'type': "breach", 
                    'source_dataset': self.source_dataset, 
                    'private_metadata': metadata}
        if use_json:
            return json.dumps(doc)
        else:
            return doc

@dataclass
class BookerWebService(BookerDocument):
    port: int
    service_name: str
    service_version: str
    source: str
    ip: str
    date: str
    def make_doc(self, use_json=False):
        metadata = {'port': self.port, 'ip': self.ip, 
                    'service': self.service, 'source': self.source,
                    'date': self.date, 'version': self.end_date}
        if self.is_public:
            doc = {'type': "web_service", 
                    'source_dataset': self.source_dataset, 
                    'metadata': metadata}
        else:
            doc = {'type': "web_service", 
                    'source_dataset': self.source_dataset, 
                    'private_metadata': metadata}
        if use_json:
            return json.dumps(doc)
        else:
            return doc

@dataclass
class BookerHost(BookerDocument):
    ip: str
    hostname: str
    operating_system: str
    date: str
    asn: int = field(init=False, kw_only=True, default=0)
    country: str = field(init=False, kw_only=True, default="")
    network_name: str = field(init=False, kw_only=True, default="")
    owner: str  = field(init=False, kw_only=True, default="")
    vulns: list[dict] = field(default_factory=list)
    services: list[dict] = field(default_factory=list)
    def make_doc(self, use_json=False):
        metadata = {'ip': self.ip, 'hostname': self.hostname, 
                    'asn': self.asn, 'owner': self.owner,
                    'date': self.date, 'network_name': self.network_name, 
                    'country': self.country, 'os': self.operating_system, 
                    'vulns': self.vulns, 'services': self.services}
        if self.is_public:
            doc = {'type': "host", 
                    'source_dataset': self.source_dataset, 
                    'metadata': metadata}
        else:
            doc = {'type': "host", 
                    'source_dataset': self.source_dataset, 
                    'private_metadata': metadata}
        if use_json:
            return json.dumps(doc)
        else:
            return doc

@dataclass
class BookerCVE(BookerDocument):
    cve_number: str
    date: str
    score: int
    host_id: str
    def make_doc(self, use_json=False):
        metadata = {'cve': cve_number, 'date': self.date, 
                    'score': self.score, 'host': self.host_id}
        if self.is_public:
            doc = {'type': "cve", 
                    'source_dataset': self.source_dataset, 
                    'metadata': metadata}
        else:
            doc = {'type': "cve", 
                    'source_dataset': self.source_dataset, 
                    'private_metadata': metadata}
        if use_json:
            return json.dumps(doc)
        else:
            return doc


@dataclass
class BookerMesaage(BookerDocument):
    platform: str # Domain of platform aka telegram.org. discord.gg
    username: str = field(kw_only=True)
    group_name: str = field(kw_only=True)
    channel_name: str = field(kw_only=True) #only used incase like discord
    message: str = field(kw_only=True)
    message_type: str = field(kw_only=True)
    is_reply: bool = field(kw_only=True)
    date: str = field(kw_only=True)

    def make_doc(self, use_json=False):
        metadata = {'platform': self.platform, 'date': self.date, 
                    'is_reply': self.is_reply, 'username': self.username, 
                    'message': self.message, 'message_type': self.message_type}
        if self.is_public:
            doc = {'type': "cve", 
                    'source_dataset': self.source_dataset, 
                    'metadata': metadata}
        else:
            doc = {'type': "cve", 
                    'source_dataset': self.source_dataset, 
                    'private_metadata': metadata}
        if use_json:
            return json.dumps(doc)
        else:
            return doc

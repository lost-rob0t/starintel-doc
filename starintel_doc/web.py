#!/usr/bin/env python3
from dataclasses import dataclass, field
from starintel_doc.documents import Document


@dataclass
class Breach(Document):
    "Deprecated, but it represents a databreach, not used."
    total: int = field(kw_only=True, default=0)
    description: str = field(kw_only=True, default="")
    url: str = field(kw_only=True, default="")


@dataclass
class Email(Document):
    user: str = field(kw_only=True, default="")
    domain: str = field(kw_only=True, default="")
    password: str = field(kw_only=True, default="")

    def set_id(self):
        # Generate a hash-based ID for Email document
        hash_data = [self.user, self.domain]
        if len(self.password) > 0:
            hash_data.append(self.password)
        self.hash_id(*hash_data)


@dataclass
class EmailMessage(Document):
    body: str = field(kw_only=True, default="")
    subject: str = field(kw_only=True, default="")
    to: str = field(kw_only=True, default="")
    from_: str = field(
        kw_only=True,
        default="",
        metadata={"dataclasses_json": {"letter_case": "camel"}},
    )
    headers: str = field(kw_only=True, default="")
    cc: list[str] = field(kw_only=True, default_factory=list)
    bcc: list[str] = field(kw_only=True, default_factory=list)

    def set_id(self):
        # Generate a hash-based ID for EmailMessage document
        self.hash_id(self.body, self.to, self.from_, self.subject)


@dataclass
class User(Document):
    url: str = field(kw_only=True)
    name: str = field(kw_only=True)
    platform: str = field(kw_only=True)
    misc: list[dict] = field(kw_only=True, default_factory=list)
    bio: str = field(kw_only=True, default="")

    def set_id(self):
        # Generate a hash-based ID for User document
        self.hash_id(self.name, self.url, self.platform)


def new_email(dataset, **kwargs):
    # Create a new Email instance and set its metadata
    email = Email(**kwargs)
    email.set_meta(dataset)
    return email


def new_email_from_string(dataset, email_str, **kwargs):
    # Create a new Email instance from email string and set its metadata
    user, domain = email_str.split("@")
    email = Email(user=user, domain=domain, **kwargs)
    email.set_meta(dataset)
    return email


def new_user(dataset, **kwargs):
    # Create a new User instance and set its metadata
    user = User(**kwargs)
    user.set_meta(dataset)
    return user

#!/usr/bin/env python3
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json, LetterCase
from starintel_doc.documents import Document


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class Message(Document):
    content: str = field(kw_only=True, default="")
    platform: str = field(kw_only=True, default="")
    user: str = field(kw_only=True, default="")
    isReply: bool = field(kw_only=True, default=False)
    media: list[str] = field(kw_only=True, default_factory=list)
    messageId: str = field(kw_only=True, default="")
    replyTo: str = field(kw_only=True, default="")
    group: str = field(kw_only=True, default="")
    channel: str = field(kw_only=True, default="")
    mentions: list[str] = field(kw_only=True, default_factory=list)

    def set_id(self):
        # Generate a hash-based ID for Message document
        self.hash_id(
            self.content,
            self.user,
            self.channel,
            self.group,
            self.messageId,
            self.platform,
        )

    def __post_init__(self):
        super().__post_init__()


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class SocialMediaPost(Document):
    content: str = field(kw_only=True, default="")
    user: str = field(kw_only=True, default="")
    replies: list[dict] = field(kw_only=True, default_factory=list)
    media: list[str] = field(kw_only=True, default_factory=list)
    replyCount: int = field(kw_only=True, default=0)
    repostCount: int = field(kw_only=True, default=0)
    url: str = field(kw_only=True, default="")
    links: list[str] = field(kw_only=True, default_factory=list)
    tags: list[str] = field(kw_only=True, default_factory=list)
    title: str = field(kw_only=True, default="")
    group: str = field(kw_only=True, default="")
    replyTo: str = field(kw_only=True, default="")

    def set_id(self):
        # Generate a hash-based ID for SocialMediaPost document
        self.hash_id(self.content, self.user, self.url, self.group)

    def __post_init__(self):
        super().__post_init__()


def new_message(dataset, **kwargs):
    # Create a new Message instance and set its metadata
    message = Message(**kwargs)
    message.set_meta(dataset)
    return message


def new_social_media_post(dataset, **kwargs):
    # Create a new SocialMediaPost instance and set its metadata
    post = SocialMediaPost(**kwargs)
    post.set_meta(dataset)
    return post

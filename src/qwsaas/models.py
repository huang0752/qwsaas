from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class JuheApiResponse:
    """Normalized Juhe API response envelope."""

    error_code: int
    error_message: str
    data: Any
    raw: dict[str, Any]


@dataclass(frozen=True)
class JuheCallbackMessage:
    """Normalized callback message without Hermes-specific runtime semantics."""

    message_id: str
    message_type: int
    text: str
    sender_id: str | None
    sender_name: str | None
    conversation_id: str | None
    at_list: tuple[str, ...]
    is_group: bool
    is_self_echo: bool
    raw_message: dict[str, Any]
    raw_event: dict[str, Any]
    attachment_kind: str | None = None
    file_name: str | None = None
    file_id: str | None = None
    file_key: str | None = None
    file_size: int | None = None
    file_md5: str | None = None
    aes_key: str | None = None
    auth_key: str | None = None
    auth_cookies: str | None = None
    download_url: str | None = None
    mime_type: str | None = None
    is_hd: bool | None = None
    base_request: dict[str, Any] | None = None
    seq: str | None = None
    appinfo: str | None = None
    referid: str | None = None
    flag: int | None = None
    content_type: int | None = None
    asid: str | None = None
    quote_appinfo: str | None = None
    quote_content: str | None = None


@dataclass(frozen=True)
class JuheCallbackEnvelope:
    """Normalized callback envelope that may contain one or more messages."""

    event_id: str | None
    guid: str | None
    notify_type: int
    messages: tuple[JuheCallbackMessage, ...]
    raw_event: dict[str, Any]
    raw_envelope: dict[str, Any]


@dataclass(frozen=True)
class DownloadedAttachment:
    """Downloaded callback attachment bytes with normalized metadata."""

    data: bytes
    file_name: str
    content_type: str


@dataclass(frozen=True)
class ResolvedAttachmentTarget:
    """Resolved callback attachment target without downloading bytes."""

    url: str
    headers: dict[str, str] | None = None
    object_url: str | None = None
    bucket: str | None = None
    key: str | None = None
    requires_object_store_auth: bool = False

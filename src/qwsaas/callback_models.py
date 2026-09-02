from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any, TypeAlias

from .callback_redaction import SafeCallbackRepr
from .enums import MessageFlagField, MsgType

ProtocolIdValue: TypeAlias = str | int | float | bool | None


class AttachmentKind(StrEnum):
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    DOCUMENT = "document"
    UNKNOWN = "unknown"


class MessageDirection(StrEnum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"
    UNKNOWN = "unknown"


class ConversationKind(StrEnum):
    DIRECT = "direct"
    ROOM = "room"
    UNKNOWN = "unknown"


class MessageRelation(StrEnum):
    ORIGINAL = "original"
    SUBSIDIARY = "subsidiary"
    UNKNOWN = "unknown"


class MessageStateKind(StrEnum):
    REVOKE = "revoke"
    READ = "read"
    DELETED = "deleted"
    ACKNOWLEDGED = "acknowledged"
    UNKNOWN = "unknown"


class MessageSource(StrEnum):
    REALTIME_11010 = "realtime_11010"
    REALTIME_11013 = "realtime_11013"
    SYNC_MSG = "sync_msg"


class IdentityFailureReason(StrEnum):
    CURRENT_ACCOUNT_MISSING = "current_account_missing"
    CURRENT_ACCOUNT_INVALID = "current_account_invalid"
    SENDER_INVALID = "sender_invalid"
    RECEIVER_INVALID = "receiver_invalid"
    ROOM_ID_INVALID = "room_id_invalid"
    ACCOUNT_NOT_PARTICIPANT = "account_not_participant"
    DIRECT_PEER_MISSING = "direct_peer_missing"
    ROOM_DIRECTION_UNVERIFIED = "room_direction_unverified"


class LogicalMessageKeySource(StrEnum):
    APPINFO = "appinfo"
    ACCOUNT_ID = "account_id"
    ACCOUNT_SEQUENCE = "account_sequence"


class LogicalMessageKeyFailure(StrEnum):
    CURRENT_ACCOUNT_REQUIRED = "current_account_required"
    CURRENT_ACCOUNT_INVALID = "current_account_invalid"
    IDENTIFIERS_MISSING = "identifiers_missing"
    IDENTIFIERS_INVALID = "identifiers_invalid"


class CallbackParseIssueCode(StrEnum):
    INVALID_FIELD = "invalid_field"
    UNKNOWN_MESSAGE_TYPE = "unknown_message_type"
    UNKNOWN_FLAG_BITS = "unknown_flag_bits"
    UNSUPPORTED_ATTACHMENT_SHAPE = "unsupported_attachment_shape"


@dataclass(frozen=True, repr=False)
class JuheCallbackParseIssue(SafeCallbackRepr):
    code: CallbackParseIssueCode
    path: str
    actual_type: str

    def to_safe_dict(self) -> dict[str, Any]:
        return {"code": self.code.value, "path": self.path, "actual_type": self.actual_type}


@dataclass(frozen=True, repr=False)
class JuheMessageProtocolFields(SafeCallbackRepr):
    id: ProtocolIdValue = field(repr=False)
    seq: ProtocolIdValue = field(repr=False)
    appinfo: ProtocolIdValue = field(repr=False)
    sender: ProtocolIdValue = field(repr=False)
    receiver: ProtocolIdValue = field(repr=False)
    roomid: ProtocolIdValue = field(repr=False)
    sendtime: int | None
    sender_name: str | None = field(repr=False)
    content_type: int | None
    referid: ProtocolIdValue = field(repr=False)
    flag: int | None
    content: Any = field(repr=False)
    at_list: tuple[str, ...] = field(repr=False)
    quote_content: str | None = field(repr=False)
    quote_appinfo: ProtocolIdValue = field(repr=False)
    send_flag: int | None
    msg_type: int | None
    asid: ProtocolIdValue = field(repr=False)

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "sendtime": self.sendtime,
            "content_type": self.content_type,
            "flag": self.flag,
            "send_flag": self.send_flag,
            "msg_type": self.msg_type,
            "has_id": self.id is not None,
            "has_seq": self.seq is not None,
            "has_appinfo": self.appinfo is not None,
        }


@dataclass(frozen=True, repr=False)
class JuheAttachment(SafeCallbackRepr):
    kind: AttachmentKind
    file_name: str | None = field(repr=False)
    file_id: str | None = field(repr=False)
    file_key: str | None = field(repr=False)
    file_size: int | None
    file_md5: str | None = field(repr=False)
    aes_key: str | None = field(repr=False)
    auth_key: str | None = field(repr=False)
    auth_cookies: str | None = field(repr=False)
    download_url: str | None = field(repr=False)
    mime_type: str | None
    is_hd: bool | None
    base_request: dict[str, Any] | None = field(repr=False)
    raw_payload: dict[str, Any] = field(repr=False)

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind.value,
            "file_size": self.file_size,
            "mime_type": self.mime_type,
            "is_hd": self.is_hd,
            "has_file_id": self.file_id is not None,
            "has_download_url": self.download_url is not None,
        }


@dataclass(frozen=True, repr=False)
class JuheCallbackMessage(SafeCallbackRepr):
    protocol: JuheMessageProtocolFields = field(repr=False)
    text: str = field(repr=False)
    sent_at: datetime | None
    message_kind: MsgType | None
    message_relation: MessageRelation
    state_kinds: frozenset[MessageStateKind]
    flags: frozenset[MessageFlagField]
    unknown_flag_bits: int
    callback_message_key: str = field(repr=False)
    batch_index: int
    source: MessageSource
    attachments: tuple[JuheAttachment, ...] = field(repr=False)
    parse_issues: tuple[JuheCallbackParseIssue, ...]
    raw_message: dict[str, Any] = field(repr=False)
    raw_event: dict[str, Any] = field(repr=False)

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "has_text": bool(self.text),
            "message_kind": self.message_kind.name if self.message_kind else None,
            "message_relation": self.message_relation.value,
            "state_kinds": sorted(item.value for item in self.state_kinds),
            "batch_index": self.batch_index,
            "source": self.source.value,
            "attachment_count": len(self.attachments),
            "issue_codes": [item.code.value for item in self.parse_issues],
        }


@dataclass(frozen=True, repr=False)
class JuheNormalizedCallbackMessage(SafeCallbackRepr):
    source: JuheCallbackMessage = field(repr=False)
    sender_id: str | None = field(repr=False)
    receiver_id: str | None = field(repr=False)
    room_id: str | None = field(repr=False)
    current_account_id: str | None = field(repr=False)
    conversation_kind: ConversationKind
    direction: MessageDirection
    contact_id: str | None = field(repr=False)
    provider_conversation_id: str | None = field(repr=False)
    account_conversation_key: str | None = field(repr=False)
    identity_failures: frozenset[IdentityFailureReason]

    @property
    def is_self_authored(self) -> bool | None:
        if self.direction is MessageDirection.OUTBOUND:
            return True
        if self.direction is MessageDirection.INBOUND:
            return False
        return None

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "conversation_kind": self.conversation_kind.value,
            "direction": self.direction.value,
            "is_self_authored": self.is_self_authored,
            "identity_failures": sorted(item.value for item in self.identity_failures),
        }


@dataclass(frozen=True, repr=False)
class JuheCallbackEnvelope(SafeCallbackRepr):
    wrapper_event_id: str | None = field(repr=False)
    guid: str | None = field(repr=False)
    notify_type: int
    notify_type_name: str
    envelope_event_key: str = field(repr=False)
    messages: tuple[JuheCallbackMessage, ...] = field(repr=False)
    parse_issues: tuple[JuheCallbackParseIssue, ...]
    raw_event: dict[str, Any] = field(repr=False)
    raw_envelope: dict[str, Any] = field(repr=False)

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "notify_type": self.notify_type,
            "notify_type_name": self.notify_type_name,
            "message_count": len(self.messages),
            "issue_codes": [item.code.value for item in self.parse_issues],
        }


@dataclass(frozen=True, repr=False)
class JuheNormalizedCallbackEnvelope(SafeCallbackRepr):
    source: JuheCallbackEnvelope = field(repr=False)
    messages: tuple[JuheNormalizedCallbackMessage, ...] = field(repr=False)

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "notify_type": self.source.notify_type,
            "message_count": len(self.messages),
            "directions": [item.direction.value for item in self.messages],
        }


@dataclass(frozen=True, repr=False)
class JuheSentMessageRef(SafeCallbackRepr):
    id: ProtocolIdValue = field(repr=False)
    seq: ProtocolIdValue = field(repr=False)
    appinfo: ProtocolIdValue = field(repr=False)
    sender: ProtocolIdValue = field(repr=False)
    receiver: ProtocolIdValue = field(repr=False)
    roomid: ProtocolIdValue = field(repr=False)
    sendtime: int | None
    flag: int | None
    asid: ProtocolIdValue = field(repr=False)

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "sendtime": self.sendtime,
            "flag": self.flag,
            "has_appinfo": self.appinfo is not None,
        }


@dataclass(frozen=True, repr=False)
class JuheLogicalMessageKey(SafeCallbackRepr):
    value: str | None = field(repr=False)
    source: LogicalMessageKeySource | None
    failure_reason: LogicalMessageKeyFailure | None

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "has_value": self.value is not None,
            "source": self.source.value if self.source else None,
            "failure_reason": self.failure_reason.value if self.failure_reason else None,
        }

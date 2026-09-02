from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any

from .callback_attachments import extract_attachments
from .callback_models import (
    CallbackParseIssueCode,
    JuheCallbackMessage,
    JuheCallbackParseIssue,
    JuheMessageProtocolFields,
    MessageRelation,
    MessageSource,
    MessageStateKind,
)
from .enums import MessageFlagField, MsgType


def parse_protocol_message(
    raw_message: Mapping[str, Any],
    *,
    source: MessageSource,
    source_event_key: str,
    item_index: int,
    raw_event: Mapping[str, Any] | None = None,
) -> JuheCallbackMessage:
    raw = dict(raw_message)
    issues: list[JuheCallbackParseIssue] = []
    msg_type = _strict_optional_int(raw.get("msg_type"))
    if msg_type is None:
        message_kind = None
        issues.append(_issue(CallbackParseIssueCode.INVALID_FIELD, "msg_type", raw.get("msg_type")))
    else:
        try:
            message_kind = MsgType(msg_type)
        except ValueError:
            message_kind = None
            issues.append(_issue(CallbackParseIssueCode.UNKNOWN_MESSAGE_TYPE, "msg_type", raw.get("msg_type")))

    flag = _strict_optional_int(raw.get("flag"))
    flags, unknown_flag_bits = _decode_flags(flag)
    if unknown_flag_bits:
        issues.append(_issue(CallbackParseIssueCode.UNKNOWN_FLAG_BITS, "flag", raw.get("flag")))

    relation = _message_relation(raw.get("referid"))
    if relation is MessageRelation.UNKNOWN:
        issues.append(_issue(CallbackParseIssueCode.INVALID_FIELD, "referid", raw.get("referid")))

    state_kinds = _state_kinds(message_kind, flags)
    attachments, attachment_issues = extract_attachments(raw, message_kind)
    issues.extend(attachment_issues)
    sendtime = _strict_optional_int(raw.get("sendtime"))
    sent_at = _sent_at(sendtime)

    protocol = JuheMessageProtocolFields(
        id=raw.get("id"),
        seq=raw.get("seq"),
        appinfo=raw.get("appinfo"),
        sender=raw.get("sender"),
        receiver=raw.get("receiver"),
        roomid=raw.get("roomid"),
        sendtime=sendtime,
        sender_name=_optional_str(raw.get("sender_name")),
        content_type=_strict_optional_int(raw.get("content_type")),
        referid=raw.get("referid"),
        flag=flag,
        content=raw.get("content"),
        at_list=_at_list(raw.get("at_list")),
        quote_content=_optional_str(raw.get("quote_content")),
        quote_appinfo=raw.get("quote_appinfo"),
        send_flag=_strict_optional_int(raw.get("send_flag")),
        msg_type=msg_type,
        asid=raw.get("asid"),
    )
    return JuheCallbackMessage(
        protocol=protocol,
        text=_extract_text(raw.get("content"), message_kind),
        sent_at=sent_at,
        message_kind=message_kind,
        message_relation=relation,
        state_kinds=state_kinds,
        flags=flags,
        unknown_flag_bits=unknown_flag_bits,
        callback_message_key=_message_fingerprint(source_event_key, item_index, raw),
        batch_index=item_index,
        source=source,
        attachments=attachments,
        parse_issues=tuple(issues),
        raw_message=raw,
        raw_event=dict(raw_event or {}),
    )


def canonical_sha256(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _message_fingerprint(source_event_key: str, item_index: int, raw: dict[str, Any]) -> str:
    return canonical_sha256(
        {"source_event_key": source_event_key, "item_index": item_index, "raw_message": raw}
    )


def _message_relation(value: Any) -> MessageRelation:
    if value is None or isinstance(value, (bool, float)):
        return MessageRelation.UNKNOWN
    if isinstance(value, int):
        if value == 0:
            return MessageRelation.ORIGINAL
        return MessageRelation.SUBSIDIARY if value > 0 else MessageRelation.UNKNOWN
    if not isinstance(value, str):
        return MessageRelation.UNKNOWN
    text = str(value).strip()
    if not text:
        return MessageRelation.UNKNOWN
    if text == "0":
        return MessageRelation.ORIGINAL
    if text.lower() in {"0.0", "null", "none"} or text.startswith(("S:", "R:")):
        return MessageRelation.UNKNOWN
    return MessageRelation.SUBSIDIARY


def _decode_flags(value: int | None) -> tuple[frozenset[MessageFlagField], int]:
    if value is None or value < 0:
        return frozenset(), 0
    known_mask = 0
    result: set[MessageFlagField] = set()
    for item in MessageFlagField.__members__.values():
        number = int(item)
        known_mask |= number
        if number and value & number == number:
            result.add(item)
    return frozenset(result), value & ~known_mask


def _state_kinds(
    message_kind: MsgType | None,
    flags: frozenset[MessageFlagField],
) -> frozenset[MessageStateKind]:
    states: set[MessageStateKind] = set()
    if message_kind is MsgType.MsgTypeRevoke:
        states.add(MessageStateKind.REVOKE)
    if message_kind is MsgType.MsgTypeReadReport:
        states.add(MessageStateKind.READ)
    if MessageFlagField.MessageFlagFieldHasRead in flags or MessageFlagField.MessageFlagFieldReadReceipt in flags:
        states.add(MessageStateKind.READ)
    if message_kind is not MsgType.MsgTypeSystem and (
        MessageFlagField.MessageFlagFieldRevoke in flags
        or MessageFlagField.MessageFlagFieldRevokeByAck in flags
    ):
        states.add(MessageStateKind.REVOKE)
    if MessageFlagField.MessageFlagFieldDel in flags:
        states.add(MessageStateKind.DELETED)
    if MessageFlagField.MessageFlagFieldAck in flags or MessageFlagField.MessageFlagFieldHadAck in flags:
        states.add(MessageStateKind.ACKNOWLEDGED)
    return frozenset(states or {MessageStateKind.UNKNOWN})


def _extract_text(value: Any, message_kind: MsgType | None) -> str:
    if message_kind is not MsgType.MsgTypeText:
        return ""
    if isinstance(value, Mapping):
        nested = value.get("msg") or value.get("text")
        return str(nested or "").strip()
    if not isinstance(value, str):
        return str(value or "").strip()
    try:
        parsed = json.loads(value)
    except (TypeError, ValueError):
        return value.strip()
    if isinstance(parsed, Mapping):
        return str(parsed.get("msg") or parsed.get("text") or "").strip()
    return value.strip()


def _strict_optional_int(value: Any) -> int | None:
    return int(value) if isinstance(value, int) and not isinstance(value, bool) else None


def _sent_at(value: int | None) -> datetime | None:
    if value is None or value < 0:
        return None
    try:
        return datetime.fromtimestamp(value, tz=UTC)
    except (OSError, OverflowError, ValueError):
        return None


def _optional_str(value: Any) -> str | None:
    if value is None or isinstance(value, bool):
        return None
    text = str(value).strip()
    return text or None


def _at_list(value: Any) -> tuple[str, ...]:
    if isinstance(value, str):
        return tuple(item.strip() for item in value.split(",") if item.strip())
    if isinstance(value, (list, tuple)):
        return tuple(str(item).strip() for item in value if str(item).strip())
    return ()


def _issue(code: CallbackParseIssueCode, path: str, value: Any) -> JuheCallbackParseIssue:
    return JuheCallbackParseIssue(code=code, path=path, actual_type=type(value).__name__)

from __future__ import annotations

import hashlib
import json
from typing import Any

from .models import JuheCallbackEnvelope, JuheCallbackMessage

NOTIFY_NEW_MESSAGE = 11010
NOTIFY_BATCH_NEW_MESSAGE = 11013
TEXT_MESSAGE_TYPE = 2


def parse_callback_envelope(payload: dict[str, Any]) -> JuheCallbackEnvelope | None:
    if not isinstance(payload, dict):
        return None

    event = _coerce_callback_event(payload.get("event"))
    if event is None:
        event = _coerce_callback_event(payload.get("data"))
    if event is None and "notify_type" in payload:
        event = payload
    if event is None:
        return None

    return parse_callback_event(
        event,
        event_id=_to_optional_str(payload.get("event_id")),
        raw_envelope=payload,
    )


def parse_callback_event(
    event: dict[str, Any],
    *,
    event_id: str | None = None,
    raw_envelope: dict[str, Any] | None = None,
) -> JuheCallbackEnvelope | None:
    if not isinstance(event, dict):
        return None

    notify_type = _to_optional_int(event.get("notify_type"))
    if notify_type is None:
        return None

    data = event.get("data")
    if isinstance(data, list):
        raw_messages = [item for item in data if isinstance(item, dict)]
    elif isinstance(data, dict):
        raw_messages = [data]
    else:
        raw_messages = []

    messages = tuple(_parse_message(message, event) for message in raw_messages)
    return JuheCallbackEnvelope(
        event_id=event_id,
        guid=_to_optional_str(event.get("guid")),
        notify_type=notify_type,
        messages=messages,
        raw_event=dict(event),
        raw_envelope=dict(raw_envelope or event),
    )


def _parse_message(message: dict[str, Any], event: dict[str, Any]) -> JuheCallbackMessage:
    sender_id = _extract_sender_id(message)
    sender_name = _to_optional_str(message.get("sender_name"))
    is_group = _is_group_message(message)
    conversation_id = _extract_conversation_id(message, sender_id, is_group)
    text = _extract_text(message)

    return JuheCallbackMessage(
        message_id=_message_id(message, event, sender_id or "", text),
        message_type=_message_type(message),
        text=text,
        sender_id=sender_id,
        sender_name=sender_name,
        conversation_id=conversation_id,
        at_list=tuple(_extract_at_list(message)),
        is_group=is_group,
        is_self_echo=_is_self_echo_message(message),
        raw_message=dict(message),
        raw_event=dict(event),
    )


def _coerce_callback_event(event: Any) -> dict[str, Any] | None:
    if isinstance(event, dict):
        return event
    if isinstance(event, str):
        text = event.strip()
        if not text:
            return None
        try:
            parsed = json.loads(text)
        except (TypeError, ValueError):
            return None
        return parsed if isinstance(parsed, dict) else None
    return None


def _message_type(message: dict[str, Any]) -> int:
    for key in ("msg_type", "msgtype", "content_type", "type"):
        value = _to_optional_int(message.get(key))
        if value is not None:
            return value
    return TEXT_MESSAGE_TYPE


def _extract_sender_id(message: dict[str, Any]) -> str | None:
    from_user = message.get("from_user") if isinstance(message.get("from_user"), dict) else {}
    sender = (
        message.get("chatroom_sender")
        or message.get("from_username")
        or message.get("sender")
        or message.get("sender_id")
        or message.get("wxid")
        or from_user.get("id")
        or ""
    )
    sender = _strip_target_prefix(str(sender).strip())
    return sender or None


def _extract_conversation_id(message: dict[str, Any], sender_id: str | None, is_group: bool) -> str | None:
    if is_group:
        group_id = _extract_group_id(message)
        return _prefixed_group(group_id) if group_id else None
    if sender_id:
        return _prefixed_dm(sender_id)
    return None


def _extract_group_id(message: dict[str, Any]) -> str:
    group_id = (
        message.get("chat_id")
        or message.get("room_id")
        or message.get("roomid")
        or message.get("chatroom")
        or ""
    )
    if _is_zero_like_id(group_id):
        return ""
    return _strip_target_prefix(str(group_id).strip())


def _is_group_message(message: dict[str, Any]) -> bool:
    if message.get("is_group") or message.get("is_chatroom_msg"):
        return True
    return bool(_extract_group_id(message))


def _extract_at_list(message: dict[str, Any]) -> list[str]:
    at_list = message.get("at_list") or []
    if isinstance(at_list, str):
        return [item.strip() for item in at_list.split(",") if item.strip()]
    if isinstance(at_list, (list, tuple, set)):
        return [str(item).strip() for item in at_list if str(item).strip()]
    return []


def _extract_text(message: dict[str, Any]) -> str:
    if _message_type(message) != TEXT_MESSAGE_TYPE:
        return ""
    raw = message.get("content")
    if raw is None:
        raw = message.get("msg", "")
    if isinstance(raw, dict):
        return str(raw.get("msg") or raw.get("text") or "").strip()
    text = str(raw or "")
    try:
        parsed = json.loads(text)
    except (TypeError, ValueError):
        return text.strip()
    if isinstance(parsed, dict):
        nested = parsed.get("data") if isinstance(parsed.get("data"), dict) else {}
        return str(parsed.get("msg") or parsed.get("text") or nested.get("msg") or "").strip()
    return text.strip()


def _message_id(message: dict[str, Any], event: dict[str, Any], sender_id: str, text: str) -> str:
    for key in ("msg_id", "msgid", "message_id", "id", "seq"):
        value = message.get(key)
        if value:
            return str(value)
    stable = "|".join(
        [
            str(event.get("guid") or ""),
            str(message.get("timestamp") or message.get("sendtime") or ""),
            sender_id,
            str(message.get("roomid") or message.get("room_id") or message.get("chat_id") or ""),
            text,
        ]
    )
    return hashlib.sha1(stable.encode("utf-8")).hexdigest()


def _prefixed_dm(value: str) -> str:
    text = str(value or "").strip()
    return text if text.upper().startswith("S:") else f"S:{text}"


def _prefixed_group(value: str) -> str:
    text = str(value or "").strip()
    return text if text.upper().startswith("R:") else f"R:{text}"


def _strip_target_prefix(value: str) -> str:
    text = str(value or "").strip()
    if text.upper().startswith(("S:", "R:")):
        return text[2:]
    return text


def _is_zero_like_id(value: Any) -> bool:
    text = str(value or "").strip()
    return text in {"", "0", "0.0", "null", "None"}


def _is_self_echo_message(message: dict[str, Any]) -> bool:
    try:
        return int(message.get("send_flag") or 0) == 1
    except (TypeError, ValueError):
        return False


def _to_optional_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _to_optional_str(value: Any) -> str | None:
    text = str(value).strip() if value is not None else ""
    return text or None

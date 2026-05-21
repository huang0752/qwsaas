from __future__ import annotations

import hashlib
import json
import mimetypes
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

from .enums import MessageFlagField, NotifyType
from .models import JuheCallbackEnvelope, JuheCallbackMessage

NOTIFY_NEW_MESSAGE = 11010
NOTIFY_BATCH_NEW_MESSAGE = 11013
TEXT_MESSAGE_TYPE = 2
IMAGE_MESSAGE_TYPE = 5
VOICE_MESSAGE_TYPE = 6
VIDEO_MESSAGE_TYPE = 7
FILE_MESSAGE_TYPE = 8

ATTACHMENT_TYPE_SPECS = {
    IMAGE_MESSAGE_TYPE: {
        "kind": "image",
        "keys": ("image", "img", "pic"),
        "default_mime": "image/jpeg",
    },
    VOICE_MESSAGE_TYPE: {
        "kind": "audio",
        "keys": ("voice", "audio"),
        "default_mime": "audio/amr",
    },
    VIDEO_MESSAGE_TYPE: {
        "kind": "video",
        "keys": ("video",),
        "default_mime": "video/mp4",
    },
    FILE_MESSAGE_TYPE: {
        "kind": "document",
        "keys": ("file", "document"),
        "default_mime": None,
    },
}


def _is_http_url(value: Any) -> bool:
    parsed = urlparse(str(value or "").strip())
    return parsed.scheme.lower() in {"http", "https"} and bool(parsed.netloc)


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
    attachment = _extract_attachment_metadata(message)

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
        attachment_kind=attachment["attachment_kind"],
        file_name=attachment["file_name"],
        file_id=attachment["file_id"],
        file_key=attachment["file_key"],
        file_size=attachment["file_size"],
        file_md5=attachment["file_md5"],
        aes_key=attachment["aes_key"],
        auth_key=attachment["auth_key"],
        download_url=attachment["download_url"],
        mime_type=attachment["mime_type"],
        is_hd=attachment["is_hd"],
        base_request=attachment["base_request"],
        seq=_to_optional_str(message.get("seq")),
        appinfo=_to_optional_str(_first_present(message, "appinfo", "app_info")),
        referid=_to_optional_str(_first_present(message, "referid", "refer_id")),
        flag=_to_optional_int(message.get("flag")),
        content_type=_to_optional_int(message.get("content_type")),
        asid=_to_optional_str(message.get("asid")),
    )


def is_original_message(message: JuheCallbackMessage) -> bool:
    referid = str(message.referid or "").strip()
    return referid in {"", "0"}


def has_message_flag(message: JuheCallbackMessage, flag: MessageFlagField | int) -> bool:
    if message.flag is None:
        return False
    return bool(int(message.flag) & int(flag))


def notify_type_name(value: NotifyType | int) -> str:
    try:
        return NotifyType(int(value)).name
    except ValueError:
        return str(int(value))


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
    raw = message.get("content")
    if raw is None:
        raw = message.get("msg", "")
    msg_type = _message_type(message)
    if isinstance(raw, dict):
        return _extract_text_from_payload(raw, allow_plain_text=msg_type == TEXT_MESSAGE_TYPE)

    text = str(raw or "")
    try:
        parsed = json.loads(text)
    except (TypeError, ValueError):
        return text.strip() if msg_type == TEXT_MESSAGE_TYPE else ""
    if isinstance(parsed, dict):
        return _extract_text_from_payload(parsed, allow_plain_text=msg_type == TEXT_MESSAGE_TYPE)
    return text.strip() if msg_type == TEXT_MESSAGE_TYPE else ""


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


def _extract_attachment_metadata(message: dict[str, Any]) -> dict[str, Any]:
    msg_type = _message_type(message)
    spec = ATTACHMENT_TYPE_SPECS.get(msg_type)
    if spec is None:
        return {
            "attachment_kind": None,
            "file_name": None,
            "file_id": None,
            "file_key": None,
            "file_size": None,
            "file_md5": None,
            "aes_key": None,
            "auth_key": None,
            "download_url": None,
            "mime_type": None,
            "is_hd": None,
            "base_request": None,
        }

    content = _coerce_message_content(message.get("content"))
    attachment = _extract_attachment_payload(message, content, spec["keys"])
    file_id = _to_optional_str(_first_present(attachment, "file_id", "fileId", "media_id", "mediaId"))
    download_url = _resolve_attachment_download_url(message, attachment, file_id)
    file_name = _to_optional_str(
        _first_present(attachment, "file_name", "filename", "name", "title")
        or _first_present(message, "file_name", "filename", "name", "title")
    )
    if file_name is None:
        file_name = _guess_attachment_name(download_url, spec["kind"])

    mime_type = _normalize_mime_type_candidate(
        _to_optional_str(_first_present(attachment, "mime_type", "content_type", "contentType"))
    )
    if mime_type is None:
        guessed_mime, _encoding = mimetypes.guess_type(file_name or download_url or "")
        mime_type = guessed_mime or spec["default_mime"]

    return {
        "attachment_kind": spec["kind"],
        "file_name": file_name,
        "file_id": file_id,
        "file_key": _to_optional_str(_first_present(attachment, "file_key", "fileKey")),
        "file_size": _to_optional_int(_first_present(attachment, "file_size", "size", "content_length")),
        "file_md5": _to_optional_str(_first_present(attachment, "file_md5", "md5", "fileMd5")),
        "aes_key": _to_optional_str(_first_present(attachment, "aes_key", "aesKey")),
        "auth_key": _to_optional_str(_first_present(attachment, "auth_key", "authKey")),
        "download_url": download_url,
        "mime_type": mime_type,
        "is_hd": _to_optional_bool(_first_present(attachment, "is_hd", "isHd")),
        "base_request": _extract_base_request(message, content, attachment),
    }


def _coerce_message_content(value: Any) -> Any:
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return ""
        try:
            return json.loads(text)
        except (TypeError, ValueError):
            return text
    return value


def _extract_attachment_payload(message: dict[str, Any], content: Any, keys: tuple[str, ...]) -> dict[str, Any]:
    containers = []
    if isinstance(content, dict):
        nested = content.get("data") if isinstance(content.get("data"), dict) else None
        containers.extend([nested, content])
    containers.append(message)

    for container in containers:
        if not isinstance(container, dict):
            continue
        cdn = container.get("cdn")
        if isinstance(cdn, dict):
            return cdn
        for key in keys:
            value = container.get(key)
            if isinstance(value, dict):
                return value
        if _looks_like_attachment_container(container):
            return container
    return {}


def _looks_like_attachment_container(value: dict[str, Any]) -> bool:
    return any(
        key in value
        for key in (
            "url",
            "download_url",
            "file_url",
            "file_name",
            "filename",
            "file_id",
            "ld_file_id",
            "file_key",
            "aes_key",
            "auth_key",
        )
    )


def _extract_base_request(*containers: Any) -> dict[str, Any] | None:
    for container in containers:
        if not isinstance(container, dict):
            continue
        value = container.get("base_request")
        if isinstance(value, dict):
            return value
    return None


def _first_present(container: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in container and container[key] not in (None, ""):
            return container[key]
    return None


def _guess_attachment_name(download_url: str | None, attachment_kind: str) -> str | None:
    if download_url:
        path = unquote(urlparse(download_url).path or "")
        name = Path(path).name
        if name and "." in name:
            return name
    fallback_names = {
        "image": "image.jpg",
        "audio": "audio.amr",
        "video": "video.mp4",
        "document": "document",
    }
    return fallback_names.get(attachment_kind)


def _resolve_attachment_download_url(
    message: dict[str, Any],
    attachment: dict[str, Any],
    file_id: str | None,
) -> str | None:
    direct_url = _to_optional_str(
        _first_present(attachment, "download_url", "url", "file_url", "fileUrl", "src", "cdn_url")
        or _first_present(message, "url", "download_url")
    )
    if direct_url:
        return direct_url

    for candidate in (
        file_id,
        _to_optional_str(_first_present(attachment, "ld_file_id", "hd_file_id")),
        _to_optional_str(_first_present(message, "file_id", "ld_file_id")),
    ):
        if candidate and _is_http_url(candidate):
            return candidate
    return None


def _normalize_mime_type_candidate(value: str | None) -> str | None:
    text = str(value or "").strip()
    if not text:
        return None
    return text if "/" in text else None


def _extract_text_from_payload(payload: dict[str, Any], *, allow_plain_text: bool) -> str:
    nested = payload.get("data") if isinstance(payload.get("data"), dict) else {}
    text = str(payload.get("msg") or payload.get("text") or nested.get("msg") or nested.get("text") or "").strip()
    if text:
        return text
    if allow_plain_text:
        return str(payload.get("content") or "").strip()
    return ""


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


def _to_optional_bool(value: Any) -> bool | None:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {"true", "1", "yes", "on"}:
        return True
    if text in {"false", "0", "no", "off"}:
        return False
    return None

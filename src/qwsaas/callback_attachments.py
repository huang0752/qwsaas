from __future__ import annotations

import json
import mimetypes
from collections.abc import Mapping
from typing import Any
from urllib.parse import urlparse

from .callback_models import (
    AttachmentKind,
    CallbackParseIssueCode,
    JuheAttachment,
    JuheCallbackParseIssue,
)
from .enums import MsgType

_SPECS: dict[MsgType, tuple[AttachmentKind, tuple[str, ...], str | None]] = {
    MsgType.MsgTypeImage: (AttachmentKind.IMAGE, ("image", "img", "pic"), "image/jpeg"),
    MsgType.MsgTypeVoice: (AttachmentKind.AUDIO, ("voice", "audio"), "audio/amr"),
    MsgType.MsgTypeVideo: (AttachmentKind.VIDEO, ("video",), "video/mp4"),
    MsgType.MsgTypeFile: (AttachmentKind.DOCUMENT, ("file", "document"), None),
}


def extract_attachments(
    raw_message: Mapping[str, Any],
    message_kind: MsgType | None,
) -> tuple[tuple[JuheAttachment, ...], tuple[JuheCallbackParseIssue, ...]]:
    if message_kind in {MsgType.MsgTypeMixed, MsgType.MsgTypeMergeMsg}:
        return (), (
            JuheCallbackParseIssue(
                CallbackParseIssueCode.UNSUPPORTED_ATTACHMENT_SHAPE,
                "content",
                type(raw_message.get("content")).__name__,
            ),
        )
    spec = _SPECS.get(message_kind) if message_kind is not None else None
    if spec is None:
        return (), ()

    kind, keys, default_mime = spec
    content = _coerce_content(raw_message.get("content"))
    payload = _find_payload(raw_message, content, keys)
    file_id = _optional_str(_first(payload, "file_id", "fileId", "media_id", "mediaId"))
    download_url = _optional_str(_first(payload, "url", "download_url", "downloadUrl"))
    if download_url is None and _is_http_url(file_id):
        download_url = file_id
    file_name = _optional_str(
        _first(payload, "file_name", "filename", "name", "title")
        or _first(raw_message, "file_name", "filename", "name", "title")
    )
    mime_type = _optional_str(_first(payload, "mime_type", "contentType"))
    if mime_type is None:
        guessed, _ = mimetypes.guess_type(file_name or download_url or "")
        mime_type = guessed or default_mime

    attachment = JuheAttachment(
        kind=kind,
        file_name=file_name,
        file_id=file_id,
        file_key=_optional_str(_first(payload, "file_key", "fileKey")),
        file_size=_optional_int(_first(payload, "file_size", "size", "content_length")),
        file_md5=_optional_str(_first(payload, "file_md5", "md5", "fileMd5")),
        aes_key=_optional_str(_first(payload, "aes_key", "aesKey")),
        auth_key=_optional_str(_first(payload, "auth_key", "authKey")),
        auth_cookies=_optional_str(_first(payload, "auth_cookies", "auth_cookie", "authCookies", "authCookie")),
        download_url=download_url,
        mime_type=mime_type,
        is_hd=_optional_bool(_first(payload, "is_hd", "isHd")),
        base_request=_mapping_or_none(_first(payload, "base_request", "baseRequest")),
        raw_payload=dict(payload),
    )
    return (attachment,), ()


def _coerce_content(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return value


def _find_payload(
    raw_message: Mapping[str, Any],
    content: Any,
    keys: tuple[str, ...],
) -> Mapping[str, Any]:
    candidates: list[Mapping[str, Any]] = []
    if isinstance(content, Mapping):
        candidates.append(content)
        nested_data = content.get("data")
        if isinstance(nested_data, Mapping):
            candidates.append(nested_data)
    candidates.append(raw_message)
    cdn = raw_message.get("cdn")
    if isinstance(cdn, Mapping):
        candidates.insert(0, cdn)
    for candidate in candidates:
        for key in keys:
            nested = candidate.get(key)
            if isinstance(nested, Mapping):
                return nested
    return candidates[0] if candidates else {}


def _first(value: Mapping[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in value and value[key] is not None:
            return value[key]
    return None


def _optional_str(value: Any) -> str | None:
    if value is None or isinstance(value, bool):
        return None
    text = str(value).strip()
    return text or None


def _optional_int(value: Any) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _optional_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        value = value.strip().lower()
    if value in (0, "0", "false"):
        return False
    if value in (1, "1", "true"):
        return True
    return None


def _mapping_or_none(value: Any) -> dict[str, Any] | None:
    return dict(value) if isinstance(value, Mapping) else None


def _is_http_url(value: Any) -> bool:
    parsed = urlparse(str(value or ""))
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)

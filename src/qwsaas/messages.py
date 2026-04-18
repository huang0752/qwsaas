from __future__ import annotations

from typing import Any, Iterable

from .client import QwSaasClient
from .exceptions import QwSaasRequestError


async def send_text(client: QwSaasClient, conversation_id: str, content: str) -> dict[str, Any]:
    """Send a text message.

    Args:
        client: Initialized QwSaasClient instance.
        conversation_id: Conversation ID, e.g. "R:<room-id>" or "S:<contact-id>".
        content: Text content to send.
    """
    if not conversation_id:
        raise QwSaasRequestError("conversation_id is required")
    if not content:
        raise QwSaasRequestError("content is required")

    return await client._request_public(
        "/msg/send_text",
        data={"conversation_id": conversation_id, "content": content},
    )


async def send_file(
    client: QwSaasClient,
    conversation_id: str,
    file_id: str,
    file_name: str,
    size: int,
    md5: str,
    aes_key: str | None = None,
) -> dict[str, Any]:
    if not conversation_id:
        raise QwSaasRequestError("conversation_id is required")
    if not file_id:
        raise QwSaasRequestError("file_id is required")
    if not file_name:
        raise QwSaasRequestError("file_name is required")
    if size <= 0:
        raise QwSaasRequestError("size must be > 0")
    if not md5:
        raise QwSaasRequestError("md5 is required")

    data: dict[str, Any] = {
        "conversation_id": conversation_id,
        "file_id": file_id,
        "file_name": file_name,
        "size": size,
        "md5": md5,
    }
    if aes_key:
        data["aes_key"] = aes_key

    return await client._request_public("/msg/send_file", data=data)


def _normalize_string_list(values: Iterable[Any]) -> list[str]:
    normalized: list[str] = []
    for value in values:
        text = str(value).strip()
        if text:
            normalized.append(text)
    return normalized


def _normalize_at_list(values: Iterable[Any]) -> list[Any]:
    normalized: list[Any] = []
    for value in values:
        if isinstance(value, int):
            normalized.append(value)
            continue
        text = str(value).strip()
        if text:
            normalized.append(text)
    return normalized


async def send_room_at(
    client: QwSaasClient,
    conversation_id: str,
    content: str,
    at_list: Iterable[Any],
) -> dict[str, Any]:
    if not conversation_id:
        raise QwSaasRequestError("conversation_id is required")
    if not content:
        raise QwSaasRequestError("content is required")

    normalized_at_list = _normalize_at_list(at_list)
    if not normalized_at_list:
        raise QwSaasRequestError("at_list is required")

    return await client._request_public(
        "/msg/send_room_at",
        data={
            "conversation_id": conversation_id,
            "content": content,
            "at_list": normalized_at_list,
        },
    )


async def confirm_msg(
    client: QwSaasClient,
    message_type: int,
    *,
    sender: str,
    receiver: str,
    msgid: str,
    roomid: str | None = None,
) -> dict[str, Any]:
    if int(message_type) < 0:
        raise QwSaasRequestError("message_type must be >= 0")
    if not sender:
        raise QwSaasRequestError("sender is required")
    if not receiver:
        raise QwSaasRequestError("receiver is required")
    if not msgid:
        raise QwSaasRequestError("msgid is required")

    data: dict[str, Any] = {
        "message_type": int(message_type),
        "sender": sender,
        "receiver": receiver,
        "msgid": msgid,
    }
    if roomid:
        data["roomid"] = roomid

    return await client._request_public("/msg/confirm_msg", data=data)


async def revoke_msg(
    client: QwSaasClient,
    conversation_id: str,
    msgid: str,
) -> dict[str, Any]:
    if not conversation_id:
        raise QwSaasRequestError("conversation_id is required")
    if not msgid:
        raise QwSaasRequestError("msgid is required")

    return await client._request_public(
        "/msg/revoke_msg",
        data={"conversation_id": conversation_id, "msgid": msgid},
    )


async def report_unread(client: QwSaasClient, conversation_id: str) -> dict[str, Any]:
    if not conversation_id:
        raise QwSaasRequestError("conversation_id is required")

    return await client._request_public(
        "/msg/report_unread",
        data={"conversation_id": conversation_id},
    )


async def send_quote_msg(
    client: QwSaasClient,
    *,
    conversation_id: str,
    quote: str,
    content: str,
    appinfo: str,
    content_type: int,
    sender: str,
    sender_name: str,
    message: dict[str, Any],
) -> dict[str, Any]:
    if not conversation_id:
        raise QwSaasRequestError("conversation_id is required")
    if not quote:
        raise QwSaasRequestError("quote is required")
    if not content:
        raise QwSaasRequestError("content is required")
    if not appinfo:
        raise QwSaasRequestError("appinfo is required")
    if int(content_type) < 0:
        raise QwSaasRequestError("content_type must be >= 0")
    if not sender:
        raise QwSaasRequestError("sender is required")
    if not sender_name:
        raise QwSaasRequestError("sender_name is required")
    if not isinstance(message, dict):
        raise QwSaasRequestError("message is required")
    if "msg_type" not in message:
        raise QwSaasRequestError("message.msg_type is required")

    payload: dict[str, Any] = {
        "conversation_id": conversation_id,
        "quote": quote,
        "content": content,
        "appinfo": appinfo,
        "content_type": int(content_type),
        "sender": sender,
        "sender_name": sender_name,
        "message": dict(message),
    }

    return await client._request_public("/msg/send_quote_msg", data=payload)

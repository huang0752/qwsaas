from __future__ import annotations

from typing import Any

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

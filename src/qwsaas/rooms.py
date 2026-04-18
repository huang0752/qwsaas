from __future__ import annotations

from typing import Any, Iterable

from .client import QwSaasClient
from .exceptions import QwSaasRequestError


async def get_room_list(
    client: QwSaasClient,
    start_index: int = 0,
    limit: int = 10,
) -> dict[str, Any]:
    if start_index < 0:
        raise QwSaasRequestError("start_index must be >= 0")
    if limit <= 0:
        raise QwSaasRequestError("limit must be > 0")
    return await client._request_public(
        "/room/get_room_list",
        data={"start_index": start_index, "limit": limit},
    )


def _normalize_string_list(values: Iterable[Any]) -> list[str]:
    normalized: list[str] = []
    for value in values:
        text = str(value).strip()
        if text:
            normalized.append(text)
    return normalized


async def batch_get_room_detail(
    client: QwSaasClient,
    room_list: Iterable[Any],
) -> dict[str, Any]:
    normalized_rooms = _normalize_string_list(room_list)
    if not normalized_rooms:
        raise QwSaasRequestError("room_list is required")

    return await client._request_public(
        "/room/batch_get_room_detail",
        data={"room_list": normalized_rooms},
    )


async def batch_get_member_detail(
    client: QwSaasClient,
    room_id: str,
    user_list: Iterable[Any],
) -> dict[str, Any]:
    if not room_id:
        raise QwSaasRequestError("room_id is required")

    normalized_users = _normalize_string_list(user_list)
    if not normalized_users:
        raise QwSaasRequestError("user_list is required")

    return await client._request_public(
        "/room/batch_get_member_detail",
        data={"room_id": room_id, "user_list": normalized_users},
    )


async def sync_room_info(
    client: QwSaasClient,
    room_id: str,
    *,
    version: int = 0,
) -> dict[str, Any]:
    if not room_id:
        raise QwSaasRequestError("room_id is required")
    if int(version) < 0:
        raise QwSaasRequestError("version must be >= 0")

    return await client._request_public(
        "/room/sync_room_info",
        data={"room_id": room_id, "version": int(version)},
    )

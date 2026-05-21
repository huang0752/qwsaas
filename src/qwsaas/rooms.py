from __future__ import annotations

from collections.abc import Mapping
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


def _payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, Mapping):
        raise QwSaasRequestError("payload must be a mapping")
    return dict(payload)


async def _post_payload(client: QwSaasClient, path: str, payload: Mapping[str, Any]) -> dict[str, Any]:
    return await client._request_public(path, data=_payload(payload))


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


async def create_outer_room(client: QwSaasClient, payload: Mapping[str, Any]) -> dict[str, Any]:
    return await _post_payload(client, "/room/create_outer_room", payload)


async def create_inner_room(client: QwSaasClient, payload: Mapping[str, Any]) -> dict[str, Any]:
    return await _post_payload(client, "/room/create_inner_room", payload)


async def create_empty_outer_room(client: QwSaasClient, payload: Mapping[str, Any]) -> dict[str, Any]:
    return await _post_payload(client, "/room/create_empty_outer_room", payload)


async def modify_room_name(client: QwSaasClient, payload: Mapping[str, Any]) -> dict[str, Any]:
    return await _post_payload(client, "/room/modify_room_name", payload)


async def invite_room_member(client: QwSaasClient, payload: Mapping[str, Any]) -> dict[str, Any]:
    return await _post_payload(client, "/room/invite_room_member", payload)


async def remove_room_member(client: QwSaasClient, payload: Mapping[str, Any]) -> dict[str, Any]:
    return await _post_payload(client, "/room/remove_room_member", payload)


async def modify_room_notice(client: QwSaasClient, payload: Mapping[str, Any]) -> dict[str, Any]:
    return await _post_payload(client, "/room/modify_room_notice", payload)


async def change_room_master(client: QwSaasClient, payload: Mapping[str, Any]) -> dict[str, Any]:
    return await _post_payload(client, "/room/change_room_master", payload)


async def room_add_admin(client: QwSaasClient, payload: Mapping[str, Any]) -> dict[str, Any]:
    return await _post_payload(client, "/room/room_add_admin", payload)


async def room_remove_admin(client: QwSaasClient, payload: Mapping[str, Any]) -> dict[str, Any]:
    return await _post_payload(client, "/room/room_remove_admin", payload)


async def modify_invite_status(client: QwSaasClient, payload: Mapping[str, Any]) -> dict[str, Any]:
    return await _post_payload(client, "/room/modify_invite_status", payload)


async def quit_room(client: QwSaasClient, payload: Mapping[str, Any]) -> dict[str, Any]:
    return await _post_payload(client, "/room/quit_room", payload)


async def dismiss_room(client: QwSaasClient, payload: Mapping[str, Any]) -> dict[str, Any]:
    return await _post_payload(client, "/room/dismiss_room", payload)


async def add_room_contact(client: QwSaasClient, payload: Mapping[str, Any]) -> dict[str, Any]:
    return await _post_payload(client, "/room/add_room_contact", payload)


async def accept_invite_url(client: QwSaasClient, payload: Mapping[str, Any]) -> dict[str, Any]:
    return await _post_payload(client, "/room/accept_invite_url", payload)


async def modify_in_room_nickname(client: QwSaasClient, payload: Mapping[str, Any]) -> dict[str, Any]:
    return await _post_payload(client, "/room/modify_in_room_nickname", payload)


async def modify_room_remark(client: QwSaasClient, payload: Mapping[str, Any]) -> dict[str, Any]:
    return await _post_payload(client, "/room/modify_room_remark", payload)


async def get_room_qrcode(client: QwSaasClient, payload: Mapping[str, Any]) -> dict[str, Any]:
    return await _post_payload(client, "/room/get_room_qrcode", payload)


async def modify_room_admin_flag(client: QwSaasClient, payload: Mapping[str, Any]) -> dict[str, Any]:
    return await _post_payload(client, "/room/modify_room_admin_flag", payload)


async def modify_room_auto_reply(client: QwSaasClient, payload: Mapping[str, Any]) -> dict[str, Any]:
    return await _post_payload(client, "/room/modify_room_auto_reply", payload)

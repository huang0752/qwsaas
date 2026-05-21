from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Iterable

from .client import QwSaasClient
from .exceptions import QwSaasRequestError


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


async def sync_contact(
    client: QwSaasClient,
    *,
    seq: str = "",
    limit: int = 10,
) -> dict[str, Any]:
    if limit <= 0:
        raise QwSaasRequestError("limit must be > 0")

    return await client._request_public(
        "/contact/sync_contact",
        data={"seq": str(seq or ""), "limit": int(limit)},
    )


async def batch_get_userinfo(
    client: QwSaasClient,
    user_list: Iterable[Any],
) -> dict[str, Any]:
    normalized_users = _normalize_string_list(user_list)
    if not normalized_users:
        raise QwSaasRequestError("user_list is required")

    return await client._request_public(
        "/contact/batch_get_userinfo",
        data={"user_list": normalized_users},
    )


async def search_contact(
    client: QwSaasClient,
    keyword: str,
    *,
    type: int = 1,
) -> dict[str, Any]:
    if not keyword:
        raise QwSaasRequestError("keyword is required")
    if int(type) <= 0:
        raise QwSaasRequestError("type must be > 0")

    return await client._request_public(
        "/contact/search_contact",
        data={"keyword": keyword, "type": int(type)},
    )


async def sync_apply_contact(
    client: QwSaasClient,
    *,
    seq: str = "",
    limit: int = 10,
) -> dict[str, Any]:
    if int(limit) <= 0:
        raise QwSaasRequestError("limit must be > 0")
    return await client._request_public(
        "/contact/sync_apply_contact",
        data={"seq": str(seq or ""), "limit": int(limit)},
    )


async def batch_get_corpinfo(client: QwSaasClient, payload: Mapping[str, Any]) -> dict[str, Any]:
    return await _post_payload(client, "/contact/batch_get_corpinfo", payload)


async def update_contact(client: QwSaasClient, payload: Mapping[str, Any]) -> dict[str, Any]:
    return await _post_payload(client, "/contact/update_contact", payload)


async def add_search_wx_contact(client: QwSaasClient, payload: Mapping[str, Any]) -> dict[str, Any]:
    return await _post_payload(client, "/contact/add_search_wx_contact", payload)


async def add_search_wx_work_contact(client: QwSaasClient, payload: Mapping[str, Any]) -> dict[str, Any]:
    return await _post_payload(client, "/contact/add_search_wx_work_contact", payload)


async def add_card_contact(client: QwSaasClient, payload: Mapping[str, Any]) -> dict[str, Any]:
    return await _post_payload(client, "/contact/add_card_contact", payload)


async def add_wx_card_contact(client: QwSaasClient, payload: Mapping[str, Any]) -> dict[str, Any]:
    return await _post_payload(client, "/contact/add_wx_card_contact", payload)


async def add_deleted_contact(client: QwSaasClient, payload: Mapping[str, Any]) -> dict[str, Any]:
    return await _post_payload(client, "/contact/add_deleted_contact", payload)


async def agree_contact(client: QwSaasClient, payload: Mapping[str, Any]) -> dict[str, Any]:
    return await _post_payload(client, "/contact/agree_contact", payload)


async def delete_contact(client: QwSaasClient, payload: Mapping[str, Any]) -> dict[str, Any]:
    return await _post_payload(client, "/contact/delete_contact", payload)


async def get_contact_by_qrcode(client: QwSaasClient, payload: Mapping[str, Any]) -> dict[str, Any]:
    return await _post_payload(client, "/contact/get_contact_by_qrcode", payload)


async def op_black_list(client: QwSaasClient, payload: Mapping[str, Any]) -> dict[str, Any]:
    return await _post_payload(client, "/contact/op_black_list", payload)

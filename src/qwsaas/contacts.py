from __future__ import annotations

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

from __future__ import annotations

from typing import Any

from .client import QwSaasClient
from .exceptions import QwSaasRequestError


async def sync_multi_data(
    client: QwSaasClient,
    *,
    business_id: int = 1,
    seq: str = "",
    limit: int = 10,
) -> dict[str, Any]:
    if int(business_id) <= 0:
        raise QwSaasRequestError("business_id must be > 0")
    if int(limit) <= 0:
        raise QwSaasRequestError("limit must be > 0")

    return await client._request_public(
        "/sync/sync_multi_data",
        data={
            "business_id": int(business_id),
            "seq": str(seq or ""),
            "limit": int(limit),
        },
    )


async def sync_msg(
    client: QwSaasClient,
    sync_key: str,
    *,
    limit: int = 100,
) -> dict[str, Any]:
    normalized_sync_key = str(sync_key or "").strip()
    if not normalized_sync_key or normalized_sync_key == "0":
        raise QwSaasRequestError("sync_key is required and must not be 0")
    if int(limit) <= 0:
        raise QwSaasRequestError("limit must be > 0")

    return await client._request_public(
        "/sync/sync_msg",
        data={"sync_key": normalized_sync_key, "limit": int(limit)},
    )

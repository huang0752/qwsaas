from __future__ import annotations

from typing import Any

from .client import QwSaasClient
from .exceptions import QwSaasRequestError


async def sync_label_list(
    client: QwSaasClient,
    *,
    seq: str = "",
    sync_type: int = 2,
) -> dict[str, Any]:
    normalized_sync_type = int(sync_type)
    if normalized_sync_type not in {1, 2}:
        raise QwSaasRequestError("sync_type must be 1 or 2")

    return await client._request_public(
        "/label/sync_label_list",
        data={"seq": str(seq or ""), "sync_type": normalized_sync_type},
    )

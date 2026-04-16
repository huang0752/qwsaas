from __future__ import annotations

from typing import Any

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

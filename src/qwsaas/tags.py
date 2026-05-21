from __future__ import annotations

from collections.abc import Mapping
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


def _payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, Mapping):
        raise QwSaasRequestError("payload must be a mapping")
    return dict(payload)


async def create_label(client: QwSaasClient, payload: Mapping[str, Any]) -> dict[str, Any]:
    return await client._request_public("/label/create_label", data=_payload(payload))


async def contact_add_label(client: QwSaasClient, payload: Mapping[str, Any]) -> dict[str, Any]:
    return await client._request_public("/label/contact_add_label", data=_payload(payload))


async def delete_label(client: QwSaasClient, payload: Mapping[str, Any]) -> dict[str, Any]:
    return await client._request_public("/label/delete_label", data=_payload(payload))


async def modify_label(client: QwSaasClient, payload: Mapping[str, Any]) -> dict[str, Any]:
    return await client._request_public("/label/modify_label", data=_payload(payload))


async def contact_add_labels(client: QwSaasClient, payload: Mapping[str, Any]) -> dict[str, Any]:
    return await client._request_public("/label/contact_add_labels", data=_payload(payload))

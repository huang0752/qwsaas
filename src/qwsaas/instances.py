from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .client import QwSaasClient
from .exceptions import QwSaasRequestError


def _payload(payload: Mapping[str, Any] | None) -> dict[str, Any]:
    if payload is None:
        return {}
    if not isinstance(payload, Mapping):
        raise QwSaasRequestError("payload must be a mapping")
    return dict(payload)


async def update_client(client: QwSaasClient, payload: Mapping[str, Any] | None = None) -> dict[str, Any]:
    return await client._request_public("/client/update_client", data=_payload(payload))


async def restore_client(client: QwSaasClient, payload: Mapping[str, Any] | None = None) -> dict[str, Any]:
    return await client._request_public("/client/restore_client", data=_payload(payload))


async def stop_client(client: QwSaasClient, payload: Mapping[str, Any] | None = None) -> dict[str, Any]:
    return await client._request_public("/client/stop_client", data=_payload(payload))


async def set_notify_url(client: QwSaasClient, payload: Mapping[str, Any] | None = None) -> dict[str, Any]:
    return await client._request_public("/client/set_notify_url", data=_payload(payload))


async def set_bridge(client: QwSaasClient, payload: Mapping[str, Any] | None = None) -> dict[str, Any]:
    return await client._request_public("/client/set_bridge", data=_payload(payload))


async def set_proxy(client: QwSaasClient, payload: Mapping[str, Any] | None = None) -> dict[str, Any]:
    return await client._request_public("/client/set_proxy", data=_payload(payload))

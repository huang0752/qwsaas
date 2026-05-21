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


async def get_profile(client: QwSaasClient, payload: Mapping[str, Any] | None = None) -> dict[str, Any]:
    return await client._request_public("/user/get_profile", data=_payload(payload))


async def get_corp_info(client: QwSaasClient, payload: Mapping[str, Any] | None = None) -> dict[str, Any]:
    return await client._request_public("/user/get_corp_info", data=_payload(payload))


async def logout(client: QwSaasClient, payload: Mapping[str, Any] | None = None) -> dict[str, Any]:
    return await client._request_public("/user/logout", data=_payload(payload))


async def get_qrcode_card_new(
    client: QwSaasClient,
    payload: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return await client._request_public("/user/get_qrcode_card_new", data=_payload(payload))


async def get_qrcode_card(
    client: QwSaasClient,
    payload: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return await client._request_public("/user/get_qrcode_card", data=_payload(payload))


async def get_bind_wxinfo(
    client: QwSaasClient,
    payload: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return await client._request_public("/user/get_bind_wxinfo", data=_payload(payload))

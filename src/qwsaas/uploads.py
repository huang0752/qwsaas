from __future__ import annotations

from typing import Any

from .client import QwSaasClient
from .exceptions import QwSaasRequestError


async def c2c_upload(
    client: QwSaasClient,
    base_request: dict[str, Any],
    file_type: int,
    url: str,
) -> dict[str, Any]:
    if not base_request:
        raise QwSaasRequestError("base_request is required")
    if file_type < 0:
        raise QwSaasRequestError("file_type must be >= 0")
    if not url:
        raise QwSaasRequestError("url is required")

    return await client._request_private(
        "/cloud/c2c_upload",
        data={
            "base_request": base_request,
            "file_type": file_type,
            "url": url,
        },
    )


async def big_upload(
    client: QwSaasClient,
    appid: str,
    auth_key: str,
    base_request: dict[str, Any],
    file_key: str,
    url: str,
    guid: str | None = None,
) -> dict[str, Any]:
    if not appid:
        raise QwSaasRequestError("appid is required")
    if not auth_key:
        raise QwSaasRequestError("auth_key is required")
    if not base_request:
        raise QwSaasRequestError("base_request is required")
    if not file_key:
        raise QwSaasRequestError("file_key is required")
    if not url:
        raise QwSaasRequestError("url is required")

    return await client._request_private(
        "/cloud/big_upload",
        data={
            "guid": guid or client.guid,
            "appid": appid,
            "auth_key": auth_key,
            "base_request": base_request,
            "file_key": file_key,
            "url": url,
        },
    )

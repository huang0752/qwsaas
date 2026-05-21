from __future__ import annotations

from collections.abc import Mapping
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


async def c2c_download(
    client: QwSaasClient,
    *,
    base_request: Mapping[str, Any],
    file_id: str,
    file_name: str,
    file_size: int,
    file_type: int,
    aes_key: str,
    to_mp3: bool = False,
) -> dict[str, Any]:
    if not base_request:
        raise QwSaasRequestError("base_request is required")
    if not file_id:
        raise QwSaasRequestError("file_id is required")
    if not file_name:
        raise QwSaasRequestError("file_name is required")
    if int(file_size) <= 0:
        raise QwSaasRequestError("file_size must be > 0")
    if int(file_type) < 0:
        raise QwSaasRequestError("file_type must be >= 0")
    if not aes_key:
        raise QwSaasRequestError("aes_key is required")

    return await client._request_private(
        "/cloud/c2c_download",
        data={
            "base_request": dict(base_request),
            "file_id": file_id,
            "file_name": file_name,
            "file_size": int(file_size),
            "file_type": int(file_type),
            "aes_key": aes_key,
            "to_mp3": bool(to_mp3),
        },
    )


async def big_download(
    client: QwSaasClient,
    *,
    base_request: Mapping[str, Any],
    url: str,
    file_name: str,
    file_size: int,
    auth_cookies: str | None = None,
) -> dict[str, Any]:
    if not base_request:
        raise QwSaasRequestError("base_request is required")
    if not url:
        raise QwSaasRequestError("url is required")
    if not file_name:
        raise QwSaasRequestError("file_name is required")
    if int(file_size) <= 0:
        raise QwSaasRequestError("file_size must be > 0")

    data: dict[str, Any] = {
        "base_request": dict(base_request),
        "url": url,
        "file_name": file_name,
        "file_size": int(file_size),
    }
    if auth_cookies:
        data["auth_cookies"] = auth_cookies
    return await client._request_private("/cloud/big_download", data=data)


async def wx_download(
    client: QwSaasClient,
    *,
    base_request: Mapping[str, Any],
    url: str,
    file_name: str,
    aes_key: str,
    auth_key: str,
) -> dict[str, Any]:
    if not base_request:
        raise QwSaasRequestError("base_request is required")
    if not url:
        raise QwSaasRequestError("url is required")
    if not file_name:
        raise QwSaasRequestError("file_name is required")
    if not aes_key:
        raise QwSaasRequestError("aes_key is required")
    if not auth_key:
        raise QwSaasRequestError("auth_key is required")

    return await client._request_private(
        "/cloud/wx_download",
        data={
            "base_request": dict(base_request),
            "url": url,
            "file_name": file_name,
            "aes_key": aes_key,
            "auth_key": auth_key,
        },
    )


async def upload_video_preview(client: QwSaasClient, payload: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, Mapping):
        raise QwSaasRequestError("payload must be a mapping")
    return await client._request_private("/cloud/add_image", data=dict(payload))

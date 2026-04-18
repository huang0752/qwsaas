from __future__ import annotations

from typing import Any

from .client import QwSaasClient
from .exceptions import QwSaasRequestError


async def get_cdn_info(client: QwSaasClient) -> dict[str, Any]:
    return await client._request_public("/cdn/get_cdn_info", data={})


async def get_wwfile_auth_key(
    client: QwSaasClient,
    file_key: str,
    file_type: int,
) -> dict[str, Any]:
    if not file_key:
        raise QwSaasRequestError("file_key is required")
    if file_type < 0:
        raise QwSaasRequestError("file_type must be >= 0")
    return await client._request_public(
        "/cdn/get_wwfile_auth_key",
        data={"file_key": file_key, "file_type": file_type},
    )


async def get_wwfile_download_info(
    client: QwSaasClient,
    file_id: str,
) -> dict[str, Any]:
    if not file_id:
        raise QwSaasRequestError("file_id is required")
    return await client._request_public(
        "/cdn/get_wwfile_download_info",
        data={"file_id": file_id},
    )


async def c2c_to_wwfile_id(
    client: QwSaasClient,
    file_id: str,
    file_md5: str,
    file_size: int,
    file_key: str,
) -> dict[str, Any]:
    if not file_id:
        raise QwSaasRequestError("file_id is required")
    if not file_md5:
        raise QwSaasRequestError("file_md5 is required")
    if file_size <= 0:
        raise QwSaasRequestError("file_size must be > 0")
    if not file_key:
        raise QwSaasRequestError("file_key is required")
    return await client._request_public(
        "/cdn/c2c_to_wwfile_id",
        data={
            "file_id": file_id,
            "file_md5": file_md5,
            "file_size": file_size,
            "file_key": file_key,
        },
    )

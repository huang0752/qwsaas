from __future__ import annotations

from typing import Any
import logging
import uuid

from .cdn import c2c_to_wwfile_id, get_cdn_info, get_wwfile_auth_key
from .exceptions import QwSaasRequestError, QwSaasResponseError
from .messages import send_file
from .uploads import big_upload, c2c_upload
from .client import QwSaasClient

logger = logging.getLogger("qwsaas.file_flows")


def _preview(value: Any, limit: int = 600) -> str:
    text = str(value)
    if len(text) <= limit:
        return text
    return f"{text[:limit]}..."


async def send_small_file_from_url(
    client: QwSaasClient,
    conversation_id: str,
    file_url: str,
    file_name: str,
    file_type: int = 5,
) -> dict[str, Any]:
    """Upload (<20m) via C2C and send file message.

    Args:
        client: Initialized QwSaasClient instance.
        conversation_id: Conversation ID, e.g. "R:<room-id>" or "S:<contact-id>".
        file_url: Source file URL.
        file_name: File name to send.
        file_type:
            1 = 图片（回调 is_hd=true）
            2 = 图片（默认）
            3 = 小程序封面
            4 = 视频
            5 = 文件、语音（默认）
    """
    if not conversation_id:
        raise QwSaasRequestError("conversation_id is required")
    if not file_url:
        raise QwSaasRequestError("file_url is required")
    if not file_name:
        raise QwSaasRequestError("file_name is required")
    if file_type < 0:
        raise QwSaasRequestError("file_type must be >= 0")

    cdn_resp = await get_cdn_info(client)
    cdn_data = cdn_resp.get("data") if isinstance(cdn_resp, dict) else None
    if not isinstance(cdn_data, dict):
        logger.error("Invalid CDN response data: %s", _preview(cdn_resp))
        raise QwSaasResponseError("Invalid CDN response data")

    try:
        base_request = {
            "cdn_dns": cdn_data["cdn_dns"],
            "client_version": cdn_data["client_version"],
            "corp_id": cdn_data["corp_id"],
            "vid": cdn_data["vid"],
        }
    except KeyError as exc:
        logger.error("Missing CDN field %s in response: %s", exc, _preview(cdn_resp))
        raise QwSaasResponseError(f"Missing CDN field: {exc}") from exc

    c2c_resp = await c2c_upload(client, base_request=base_request, file_type=file_type, url=file_url)
    c2c_data = c2c_resp.get("data") if isinstance(c2c_resp, dict) else None
    if not isinstance(c2c_data, dict):
        logger.error("Invalid C2C response data: %s", _preview(c2c_resp))
        raise QwSaasResponseError("Invalid C2C response data")

    try:
        file_id = c2c_data["file_id"]
        file_size = c2c_data["file_size"]
        file_md5 = c2c_data["file_md5"]
        aes_key = c2c_data["aes_key"]
    except KeyError as exc:
        logger.error("Missing C2C field %s in response: %s", exc, _preview(c2c_resp))
        raise QwSaasResponseError(f"Missing C2C field: {exc}") from exc

    return await send_file(
        client,
        conversation_id=conversation_id,
        file_id=file_id,
        file_name=file_name,
        size=file_size,
        md5=file_md5,
        aes_key=aes_key,
    )


async def send_big_file_from_url(
    client: QwSaasClient,
    conversation_id: str,
    file_url: str,
    file_name: str,
    file_type: int = 5,
) -> dict[str, Any]:
    """Upload (>20m) via bigcdn and send file message.

    Args:
        client: Initialized QwSaasClient instance (private_base_url required).
        conversation_id: Conversation ID, e.g. "R:<room-id>" or "S:<contact-id>".
        file_url: Source file URL.
        file_name: File name to send.
        file_type:
            1 = 图片（回调 is_hd=true）
            2 = 图片（默认）
            3 = 小程序封面
            4 = 视频
            5 = 文件、语音（默认）
    """
    if not conversation_id:
        raise QwSaasRequestError("conversation_id is required")
    if not file_url:
        raise QwSaasRequestError("file_url is required")
    if not file_name:
        raise QwSaasRequestError("file_name is required")
    if file_type < 0:
        raise QwSaasRequestError("file_type must be >= 0")

    file_key = str(uuid.uuid4()).upper()

    cdn_resp = await get_cdn_info(client)
    cdn_data = cdn_resp.get("data") if isinstance(cdn_resp, dict) else None
    if not isinstance(cdn_data, dict):
        logger.error("Invalid CDN response data: %s", _preview(cdn_resp))
        raise QwSaasResponseError("Invalid CDN response data")

    try:
        base_request = {
            "cdn_dns": cdn_data["cdn_dns"],
            "client_version": cdn_data["client_version"],
            "corp_id": cdn_data["corp_id"],
            "vid": cdn_data["vid"],
        }
    except KeyError as exc:
        logger.error("Missing CDN field %s in response: %s", exc, _preview(cdn_resp))
        raise QwSaasResponseError(f"Missing CDN field: {exc}") from exc

    auth_resp = await get_wwfile_auth_key(client, file_key=file_key, file_type=file_type)
    auth_data = auth_resp.get("data") if isinstance(auth_resp, dict) else None
    if not isinstance(auth_data, dict):
        logger.error("Invalid auth response data: %s", _preview(auth_resp))
        raise QwSaasResponseError("Invalid auth response data")
    try:
        appid = auth_data["appid"]
        auth_key = auth_data["auth_key"]
    except KeyError as exc:
        logger.error("Missing auth field %s in response: %s", exc, _preview(auth_resp))
        raise QwSaasResponseError(f"Missing auth field: {exc}") from exc

    big_resp = await big_upload(
        client,
        appid=appid,
        auth_key=auth_key,
        base_request=base_request,
        file_key=file_key,
        url=file_url,
    )
    big_data = big_resp.get("data") if isinstance(big_resp, dict) else None
    if not isinstance(big_data, dict):
        logger.error("Invalid big upload response data: %s", _preview(big_resp))
        raise QwSaasResponseError("Invalid big upload response data")

    try:
        c2c_file_id = big_data["file_id"]
        file_size = big_data["file_size"]
        file_md5 = big_data["file_md5"]
        upload_file_key = big_data["file_key"]
    except KeyError as exc:
        logger.error("Missing big upload field %s in response: %s", exc, _preview(big_resp))
        raise QwSaasResponseError(f"Missing big upload field: {exc}") from exc

    c2c_resp = await c2c_to_wwfile_id(
        client,
        file_id=c2c_file_id,
        file_md5=file_md5,
        file_size=file_size,
        file_key=upload_file_key,
    )
    c2c_data = c2c_resp.get("data") if isinstance(c2c_resp, dict) else None
    if not isinstance(c2c_data, dict):
        logger.error("Invalid C2C-to-WW response data: %s", _preview(c2c_resp))
        raise QwSaasResponseError("Invalid C2C-to-WW response data")
    try:
        ww_file_id = c2c_data["file_id"]
    except KeyError as exc:
        logger.error("Missing C2C-to-WW field %s in response: %s", exc, _preview(c2c_resp))
        raise QwSaasResponseError(f"Missing C2C-to-WW field: {exc}") from exc

    return await send_file(
        client,
        conversation_id=conversation_id,
        file_id=ww_file_id,
        file_name=file_name,
        size=file_size,
        md5=file_md5,
    )

from __future__ import annotations

from pathlib import Path
import tempfile
from typing import Any
import logging
import uuid
from urllib.parse import unquote, urlparse

import httpx

from .cdn import c2c_to_wwfile_id, get_cdn_info, get_wwfile_auth_key
from .exceptions import QwSaasRequestError, QwSaasResponseError, QwSaasStorageConfigError
from .messages import send_file
from .uploads import big_upload, c2c_upload
from .client import QwSaasClient

logger = logging.getLogger("qwsaas.file_flows")
SMALL_FILE_LIMIT_BYTES = 20 * 1024 * 1024


def _preview(value: Any, limit: int = 600) -> str:
    text = str(value)
    if len(text) <= limit:
        return text
    return f"{text[:limit]}..."


def _source_name(value: str, default: str = "attachment") -> str:
    parsed = urlparse(str(value or ""))
    name = Path(unquote(parsed.path or "")).name if parsed.path else ""
    return name or default


def _looks_like_signed_http_url(value: str) -> bool:
    parsed = urlparse(str(value or ""))
    if parsed.scheme.lower() not in {"http", "https"}:
        return False
    query = parsed.query.lower()
    return any(
        token in query
        for token in (
            "x-amz-signature=",
            "x-amz-credential=",
            "expires=",
            "signature=",
            "token=",
        )
    )


async def _get_remote_file_size_hint(file_url: str, timeout_seconds: float = 15.0) -> int | None:
    try:
        async with httpx.AsyncClient(timeout=timeout_seconds, follow_redirects=True) as http_client:
            response = await http_client.head(file_url)
    except httpx.HTTPError:
        return None
    if response.status_code >= 400:
        return None
    content_length = response.headers.get("content-length")
    if not content_length:
        return None
    try:
        size = int(content_length)
    except ValueError:
        return None
    return size if size >= 0 else None


def _ensure_storage(client_or_storage: Any, storage: Any | None = None) -> Any:
    object_storage = storage if storage is not None else getattr(client_or_storage, "storage", None)
    if object_storage is None:
        raise QwSaasStorageConfigError("storage is required for local file staging")
    for method_name in ("upload_file", "presign_get_url", "delete_object"):
        if not hasattr(object_storage, method_name):
            raise QwSaasStorageConfigError(f"storage.{method_name} is required")
    return object_storage


async def _download_remote_to_temp(
    file_url: str,
    *,
    file_name: str,
    timeout_seconds: float = 30.0,
) -> Path:
    try:
        async with httpx.AsyncClient(timeout=timeout_seconds, follow_redirects=True) as http_client:
            response = await http_client.get(file_url)
    except httpx.HTTPError as exc:
        raise QwSaasResponseError(f"download signed URL failed: {exc}") from exc
    if response.status_code >= 400:
        raise QwSaasResponseError(f"download signed URL failed with HTTP {response.status_code}")

    suffix = Path(file_name).suffix
    handle = tempfile.NamedTemporaryFile(prefix="qwsaas-restage-", suffix=suffix, delete=False)
    try:
        handle.write(response.content)
        return Path(handle.name)
    finally:
        handle.close()


async def send_file_from_url(
    client: QwSaasClient,
    conversation_id: str,
    file_url: str,
    file_name: str | None = None,
    *,
    file_type: int = 5,
    size_hint_bytes: int | None = None,
    restage_signed_url: bool = False,
    storage: Any | None = None,
) -> dict[str, Any]:
    if not conversation_id:
        raise QwSaasRequestError("conversation_id is required")
    if not file_url:
        raise QwSaasRequestError("file_url is required")
    if int(file_type) < 0:
        raise QwSaasRequestError("file_type must be >= 0")

    resolved_name = file_name or _source_name(file_url)
    if restage_signed_url or _looks_like_signed_http_url(file_url) and storage is not None:
        temp_path = await _download_remote_to_temp(file_url, file_name=resolved_name)
        try:
            return await send_file_from_path(
                client,
                conversation_id,
                temp_path,
                file_name=resolved_name,
                file_type=file_type,
                cleanup=True,
                storage=storage,
            )
        finally:
            temp_path.unlink(missing_ok=True)

    size_hint = size_hint_bytes
    if size_hint is None:
        size_hint = await _get_remote_file_size_hint(file_url)

    if size_hint is not None and int(size_hint) > SMALL_FILE_LIMIT_BYTES:
        return await send_big_file_from_url(
            client,
            conversation_id=conversation_id,
            file_url=file_url,
            file_name=resolved_name,
            file_type=file_type,
        )

    return await send_small_file_from_url(
        client,
        conversation_id=conversation_id,
        file_url=file_url,
        file_name=resolved_name,
        file_type=file_type,
    )


async def send_image_from_url(
    client: QwSaasClient,
    conversation_id: str,
    image_url: str,
    file_name: str | None = None,
    *,
    file_type: int = 2,
    size_hint_bytes: int | None = None,
) -> dict[str, Any]:
    return await send_file_from_url(
        client,
        conversation_id=conversation_id,
        file_url=image_url,
        file_name=file_name or _source_name(image_url),
        file_type=file_type,
        size_hint_bytes=size_hint_bytes,
    )


async def send_video_from_url(
    client: QwSaasClient,
    conversation_id: str,
    video_url: str,
    file_name: str | None = None,
    *,
    file_type: int = 4,
    size_hint_bytes: int | None = None,
) -> dict[str, Any]:
    return await send_file_from_url(
        client,
        conversation_id=conversation_id,
        file_url=video_url,
        file_name=file_name or _source_name(video_url),
        file_type=file_type,
        size_hint_bytes=size_hint_bytes,
    )


async def send_voice_from_url(
    client: QwSaasClient,
    conversation_id: str,
    voice_url: str,
    file_name: str | None = None,
    *,
    file_type: int = 5,
    size_hint_bytes: int | None = None,
) -> dict[str, Any]:
    return await send_file_from_url(
        client,
        conversation_id=conversation_id,
        file_url=voice_url,
        file_name=file_name or _source_name(voice_url),
        file_type=file_type,
        size_hint_bytes=size_hint_bytes,
    )


async def send_file_from_path(
    client: QwSaasClient,
    conversation_id: str,
    file_path: str | Path,
    file_name: str | None = None,
    *,
    file_type: int = 5,
    cleanup: bool = True,
    storage: Any | None = None,
) -> dict[str, Any]:
    path = Path(file_path)
    if not path.is_file():
        raise QwSaasRequestError(f"file_path does not exist: {path}")

    object_storage = _ensure_storage(client, storage)
    stored = object_storage.upload_file(path)
    signed_url = object_storage.presign_get_url(stored.bucket, stored.key)
    try:
        return await send_file_from_url(
            client,
            conversation_id=conversation_id,
            file_url=signed_url,
            file_name=file_name or path.name,
            file_type=file_type,
            size_hint_bytes=stored.size,
            restage_signed_url=False,
        )
    finally:
        if cleanup:
            object_storage.delete_object(stored.bucket, stored.key)


async def send_image_from_path(
    client: QwSaasClient,
    conversation_id: str,
    image_path: str | Path,
    file_name: str | None = None,
    *,
    file_type: int = 2,
    cleanup: bool = True,
    storage: Any | None = None,
) -> dict[str, Any]:
    return await send_file_from_path(
        client,
        conversation_id,
        image_path,
        file_name=file_name,
        file_type=file_type,
        cleanup=cleanup,
        storage=storage,
    )


async def send_video_from_path(
    client: QwSaasClient,
    conversation_id: str,
    video_path: str | Path,
    file_name: str | None = None,
    *,
    file_type: int = 4,
    cleanup: bool = True,
    storage: Any | None = None,
) -> dict[str, Any]:
    return await send_file_from_path(
        client,
        conversation_id,
        video_path,
        file_name=file_name,
        file_type=file_type,
        cleanup=cleanup,
        storage=storage,
    )


async def send_voice_from_path(
    client: QwSaasClient,
    conversation_id: str,
    voice_path: str | Path,
    file_name: str | None = None,
    *,
    file_type: int = 5,
    cleanup: bool = True,
    storage: Any | None = None,
) -> dict[str, Any]:
    return await send_file_from_path(
        client,
        conversation_id,
        voice_path,
        file_name=file_name,
        file_type=file_type,
        cleanup=cleanup,
        storage=storage,
    )


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

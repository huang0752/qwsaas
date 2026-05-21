from __future__ import annotations

import mimetypes
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

import httpx

from .cdn import get_cdn_info, get_wwfile_download_info
from .exceptions import (
    QwSaasPrivateObjectAccessError,
    QwSaasRequestError,
    QwSaasResponseError,
)
from .models import DownloadedAttachment, ResolvedAttachmentTarget


@dataclass(frozen=True)
class _ResolvedDownloadTarget:
    url: str
    headers: dict[str, str] | None = None
    requires_object_store_auth: bool = False


def _looks_like_private_media_url(download_url: str) -> bool:
    parsed = urlparse(download_url)
    host = parsed.netloc.lower()
    path = parsed.path.lower()
    return host.endswith("weixin.qq.com") or "tpdownloadmedia" in path


def _looks_like_public_qpic_url(download_url: str) -> bool:
    host = urlparse(download_url).netloc.lower()
    return host.startswith("wework.qpic.cn") or host.endswith(".qpic.cn")


def _looks_like_c2c_file_id(file_id: str) -> bool:
    return str(file_id or "").strip().startswith("30")


def _looks_like_big_file_id(file_id: str) -> bool:
    return str(file_id or "").strip().startswith("*")


def _normalize_file_name(file_name: str | None, download_url: str) -> str:
    text = str(file_name or "").strip()
    if text:
        return Path(text).name or "attachment"

    path = unquote(urlparse(download_url).path or "")
    derived = Path(path).name
    return derived or "attachment"


def _normalize_content_type(value: str | None, fallback_name: str, download_url: str) -> str:
    text = str(value or "").strip()
    if text:
        return text.split(";", 1)[0].strip()
    guessed, _encoding = mimetypes.guess_type(fallback_name or download_url)
    return guessed or "application/octet-stream"


def _extract_private_download_url(body: dict[str, Any]) -> str:
    data = body.get("data") if isinstance(body.get("data"), dict) else {}
    url = str(data.get("url") or body.get("url") or "").strip()
    if not url:
        raise QwSaasResponseError("Private download response missing data.url")
    return url


def _extract_big_download_target(body: dict[str, Any]) -> _ResolvedDownloadTarget:
    data = body.get("data") if isinstance(body.get("data"), dict) else {}
    url = str(data.get("url") or body.get("url") or "").strip()
    if not url:
        raise QwSaasResponseError("Big download response missing data.url")

    auth_cookie = str(data.get("auth_cookie") or body.get("auth_cookie") or "").strip()
    headers: dict[str, str] | None = None
    if auth_cookie and "authkey=" not in url:
        headers = {"Cookie": auth_cookie.replace("&", "; ")}
    return _ResolvedDownloadTarget(url=url, headers=headers)


def _c2c_file_type(
    *,
    attachment_kind: str | None,
    mime_type: str | None,
    is_hd: bool | None,
) -> int:
    kind = str(attachment_kind or "").strip().lower()
    normalized_mime = str(mime_type or "").strip().lower()
    if kind == "image" or normalized_mime.startswith("image/"):
        return 1 if is_hd else 2
    if kind == "video" or normalized_mime.startswith("video/"):
        return 4
    return 5


def _looks_like_http_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme.lower() in {"http", "https"} and bool(parsed.netloc)


async def _download_bytes(
    url: str,
    *,
    timeout_seconds: float,
    headers: dict[str, str] | None = None,
    requires_object_store_auth: bool = False,
) -> httpx.Response:
    try:
        async with httpx.AsyncClient(timeout=timeout_seconds, follow_redirects=True) as http_client:
            response = await http_client.get(url, headers=headers)
    except httpx.HTTPError as exc:
        raise QwSaasResponseError(f"download failed: {exc}") from exc

    if response.status_code >= 400:
        if requires_object_store_auth and response.status_code in {401, 403}:
            raise QwSaasPrivateObjectAccessError(
                "resolved private object is not publicly readable; "
                "authenticated object storage access is required to fetch the inbound attachment",
                object_url=url,
                status_code=response.status_code,
            )
        response.raise_for_status()
    return response


async def _resolve_base_request(client: Any, base_request: dict[str, Any] | None) -> dict[str, Any]:
    if isinstance(base_request, dict):
        required = ("cdn_dns", "client_version", "corp_id", "vid")
        if all(str(base_request.get(key) or "").strip() for key in required):
            return {key: str(base_request[key]) for key in required}

    if client is None or not hasattr(client, "_request_public"):
        raise QwSaasRequestError(
            "private attachment download requires base_request or a client with _request_public"
        )

    body = await get_cdn_info(client)
    data = body.get("data") if isinstance(body.get("data"), dict) else None
    if not isinstance(data, dict):
        raise QwSaasResponseError("Invalid CDN info response data")

    try:
        return {
            "cdn_dns": str(data["cdn_dns"]),
            "client_version": str(data["client_version"]),
            "corp_id": str(data["corp_id"]),
            "vid": str(data["vid"]),
        }
    except KeyError as exc:
        raise QwSaasResponseError(f"Missing CDN info field: {exc}") from exc


async def download_callback_attachment(
    client: Any,
    *,
    download_url: str,
    file_id: str | None = None,
    file_name: str | None = None,
    file_size: int | None = None,
    aes_key: str | None = None,
    auth_key: str | None = None,
    attachment_kind: str | None = None,
    mime_type: str | None = None,
    is_hd: bool | None = None,
    base_request: dict[str, Any] | None = None,
    max_bytes: int | None = None,
    timeout_seconds: float = 30.0,
) -> DownloadedAttachment:
    url = str(download_url or "").strip()
    normalized_file_id = str(file_id or "").strip()
    if not url and not normalized_file_id:
        raise QwSaasRequestError("download_url or file_id is required")

    if file_size is not None and max_bytes is not None and int(file_size) > int(max_bytes):
        raise QwSaasRequestError(
            f"attachment exceeds max_bytes ({int(file_size)} > {int(max_bytes)})"
        )

    resolved_target = await resolve_callback_attachment_target(
        client,
        download_url=download_url,
        file_id=file_id,
        file_name=file_name,
        file_size=file_size,
        aes_key=aes_key,
        auth_key=auth_key,
        attachment_kind=attachment_kind,
        mime_type=mime_type,
        is_hd=is_hd,
        base_request=base_request,
    )

    response = await _download_bytes(
        resolved_target.url,
        timeout_seconds=timeout_seconds,
        headers=resolved_target.headers,
        requires_object_store_auth=resolved_target.requires_object_store_auth,
    )

    normalized_name = _normalize_file_name(file_name, resolved_target.url)
    return DownloadedAttachment(
        data=response.content,
        file_name=normalized_name,
        content_type=_normalize_content_type(
            response.headers.get("content-type"),
            normalized_name,
            resolved_target.url,
        ),
    )


async def resolve_callback_attachment_target(
    client: Any,
    *,
    download_url: str,
    file_id: str | None = None,
    file_name: str | None = None,
    file_size: int | None = None,
    aes_key: str | None = None,
    auth_key: str | None = None,
    attachment_kind: str | None = None,
    mime_type: str | None = None,
    is_hd: bool | None = None,
    base_request: dict[str, Any] | None = None,
    storage: Any | None = None,
) -> ResolvedAttachmentTarget:
    url = str(download_url or "").strip()
    normalized_file_id = str(file_id or "").strip()
    if not url and not normalized_file_id:
        raise QwSaasRequestError("download_url or file_id is required")

    resolved_target = _ResolvedDownloadTarget(url=url)
    if normalized_file_id and _looks_like_big_file_id(normalized_file_id):
        if client is None or not hasattr(client, "_request_public"):
            raise QwSaasRequestError("client._request_public is required for big file attachment downloads")
        body = await get_wwfile_download_info(client, normalized_file_id)
        resolved_target = _extract_big_download_target(body)
    elif normalized_file_id and _looks_like_c2c_file_id(normalized_file_id):
        if not str(aes_key or "").strip():
            raise QwSaasRequestError("c2c attachment download requires aes_key")
        if file_size is None:
            raise QwSaasRequestError("c2c attachment download requires file_size")
        if client is None or not hasattr(client, "_request_private"):
            raise QwSaasRequestError("client._request_private is required for c2c attachment downloads")
        resolved_base_request = await _resolve_base_request(client, base_request)
        body = await client._request_private(
            "/cloud/c2c_download",
            data={
                "file_id": normalized_file_id,
                "file_name": _normalize_file_name(file_name, normalized_file_id),
                "file_size": int(file_size),
                "file_type": _c2c_file_type(
                    attachment_kind=attachment_kind,
                    mime_type=mime_type,
                    is_hd=is_hd,
                ),
                "aes_key": str(aes_key),
                "to_mp3": False,
                "base_request": resolved_base_request,
            },
        )
        resolved_target = _ResolvedDownloadTarget(
            url=_extract_private_download_url(body),
            requires_object_store_auth=True,
        )
    elif normalized_file_id and _looks_like_http_url(normalized_file_id) and not _looks_like_public_qpic_url(normalized_file_id):
        if not str(aes_key or "").strip() or not str(auth_key or "").strip():
            raise QwSaasRequestError(
                "private attachment download requires aes_key and auth_key"
            )
        if client is None or not hasattr(client, "_request_private"):
            raise QwSaasRequestError("client._request_private is required for private attachment downloads")
        resolved_base_request = await _resolve_base_request(client, base_request)
        body = await client._request_private(
            "/cloud/wx_download",
            data={
                "url": normalized_file_id,
                "file_name": _normalize_file_name(file_name, normalized_file_id),
                "aes_key": str(aes_key),
                "auth_key": str(auth_key),
                "base_request": resolved_base_request,
            },
        )
        resolved_target = _ResolvedDownloadTarget(
            url=_extract_private_download_url(body),
            requires_object_store_auth=True,
        )
    elif url and _looks_like_private_media_url(url):
        if not str(aes_key or "").strip() or not str(auth_key or "").strip():
            raise QwSaasRequestError(
                "private attachment download requires aes_key and auth_key"
            )
        if client is None or not hasattr(client, "_request_private"):
            raise QwSaasRequestError("client._request_private is required for private attachment downloads")
        resolved_base_request = await _resolve_base_request(client, base_request)
        body = await client._request_private(
            "/cloud/wx_download",
            data={
                "url": url,
                "file_name": _normalize_file_name(file_name, url),
                "aes_key": str(aes_key),
                "auth_key": str(auth_key),
                "base_request": resolved_base_request,
            },
        )
        resolved_target = _ResolvedDownloadTarget(
            url=_extract_private_download_url(body),
            requires_object_store_auth=True,
        )
    elif not resolved_target.url and normalized_file_id and _looks_like_http_url(normalized_file_id):
        resolved_target = _ResolvedDownloadTarget(url=normalized_file_id)

    if not resolved_target.url:
        raise QwSaasRequestError(f"unsupported attachment reference: {normalized_file_id or url}")

    return _with_object_storage_target(client, resolved_target, storage=storage)


def _with_object_storage_target(
    client: Any,
    target: _ResolvedDownloadTarget,
    *,
    storage: Any | None,
) -> ResolvedAttachmentTarget:
    if not target.requires_object_store_auth:
        return ResolvedAttachmentTarget(url=target.url, headers=target.headers)

    object_storage = storage if storage is not None else getattr(client, "storage", None)
    if object_storage is None:
        return ResolvedAttachmentTarget(
            url=target.url,
            headers=target.headers,
            object_url=target.url,
            requires_object_store_auth=True,
        )

    try:
        bucket, key = object_storage.parse_object_url(target.url)
        signed_url = object_storage.presign_get_url(bucket, key)
    except Exception:
        return ResolvedAttachmentTarget(
            url=target.url,
            headers=target.headers,
            object_url=target.url,
            requires_object_store_auth=True,
        )

    return ResolvedAttachmentTarget(
        url=signed_url,
        headers=target.headers,
        object_url=target.url,
        bucket=bucket,
        key=key,
        requires_object_store_auth=False,
    )

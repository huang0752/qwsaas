from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from qwsaas.exceptions import QwSaasRequestError
from qwsaas.uploads import (
    big_download,
    c2c_download,
    upload_video_preview,
    wx_download,
)


BASE_REQUEST = {
    "cdn_dns": "cdn",
    "client_version": "5.0.0",
    "corp_id": "corp",
    "vid": "vid",
}


@pytest.mark.asyncio
async def test_c2c_download_posts_expected_private_payload() -> None:
    client = SimpleNamespace(_request_private=AsyncMock(return_value={"ok": True}))

    await c2c_download(
        client,
        base_request=BASE_REQUEST,
        file_id="30-file-id",
        file_name="image.jpg",
        file_size=123,
        file_type=2,
        aes_key="aes",
        to_mp3=True,
    )

    client._request_private.assert_awaited_once_with(
        "/cloud/c2c_download",
        data={
            "base_request": BASE_REQUEST,
            "file_id": "30-file-id",
            "file_name": "image.jpg",
            "file_size": 123,
            "file_type": 2,
            "aes_key": "aes",
            "to_mp3": True,
        },
    )


@pytest.mark.asyncio
async def test_c2c_download_validates_required_fields() -> None:
    client = SimpleNamespace(_request_private=AsyncMock())

    with pytest.raises(QwSaasRequestError, match="file_id"):
        await c2c_download(
            client,
            base_request=BASE_REQUEST,
            file_id="",
            file_name="image.jpg",
            file_size=123,
            file_type=2,
            aes_key="aes",
        )


@pytest.mark.asyncio
async def test_big_download_preserves_optional_auth_cookies() -> None:
    client = SimpleNamespace(_request_private=AsyncMock(return_value={"ok": True}))

    await big_download(
        client,
        base_request=BASE_REQUEST,
        url="*big-file-id",
        file_name="archive.zip",
        file_size=456,
        auth_cookies="authkey=token",
    )

    client._request_private.assert_awaited_once_with(
        "/cloud/big_download",
        data={
            "base_request": BASE_REQUEST,
            "url": "*big-file-id",
            "file_name": "archive.zip",
            "file_size": 456,
            "auth_cookies": "authkey=token",
        },
    )


@pytest.mark.asyncio
async def test_wx_download_posts_expected_private_payload() -> None:
    client = SimpleNamespace(_request_private=AsyncMock(return_value={"ok": True}))

    await wx_download(
        client,
        base_request=BASE_REQUEST,
        url="https://imunion.weixin.qq.com/file",
        file_name="report.docx",
        aes_key="aes",
        auth_key="auth",
    )

    client._request_private.assert_awaited_once_with(
        "/cloud/wx_download",
        data={
            "base_request": BASE_REQUEST,
            "url": "https://imunion.weixin.qq.com/file",
            "file_name": "report.docx",
            "aes_key": "aes",
            "auth_key": "auth",
        },
    )


@pytest.mark.asyncio
async def test_upload_video_preview_preserves_unknown_payload_fields() -> None:
    client = SimpleNamespace(_request_private=AsyncMock(return_value={"ok": True}))

    await upload_video_preview(client, {"url": "https://file.example/cover.jpg", "extra": "keep"})

    client._request_private.assert_awaited_once_with(
        "/cloud/add_image",
        data={"url": "https://file.example/cover.jpg", "extra": "keep"},
    )

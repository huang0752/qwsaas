from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock

import httpx
import pytest

from qwsaas.exceptions import QwSaasRequestError
from qwsaas.inbound_downloads import download_callback_attachment, resolve_callback_attachment_target


class DummyResponse:
    def __init__(
        self,
        *,
        status_code: int = 200,
        content: bytes = b"file-bytes",
        headers: dict[str, str] | None = None,
        text: str = "",
    ) -> None:
        self.status_code = status_code
        self.content = content
        self.headers = headers or {"content-type": "application/pdf"}
        self.text = text or content.decode("utf-8", errors="ignore")

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            request = httpx.Request("GET", "https://download.example/test")
            response = httpx.Response(
                self.status_code,
                request=request,
                content=self.content,
                headers=self.headers,
            )
            raise httpx.HTTPStatusError(
                f"HTTP {self.status_code}",
                request=request,
                response=response,
            )


def patch_async_client(monkeypatch: pytest.MonkeyPatch, response: DummyResponse) -> dict[str, Any]:
    calls: dict[str, Any] = {}

    class FakeAsyncClient:
        def __init__(self, *, timeout: float, follow_redirects: bool) -> None:
            calls["timeout"] = timeout
            calls["follow_redirects"] = follow_redirects

        async def __aenter__(self) -> "FakeAsyncClient":
            return self

        async def __aexit__(self, *args: object) -> None:
            return None

        async def get(self, url: str, headers: dict[str, str] | None = None) -> DummyResponse:
            calls["url"] = url
            calls["headers"] = headers
            return response

    monkeypatch.setattr("qwsaas.inbound_downloads.httpx.AsyncClient", FakeAsyncClient)
    return calls


@pytest.mark.asyncio
async def test_download_callback_attachment_fetches_direct_url(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = patch_async_client(monkeypatch, DummyResponse(content=b"%PDF", headers={"content-type": "application/pdf"}))
    client = SimpleNamespace(_request_private=AsyncMock())

    result = await download_callback_attachment(
        client,
        download_url="https://files.example/report.pdf",
        file_name="report.pdf",
        file_size=4,
        max_bytes=1024,
    )

    assert result.data == b"%PDF"
    assert result.file_name == "report.pdf"
    assert result.content_type == "application/pdf"
    assert calls["url"] == "https://files.example/report.pdf"
    client._request_private.assert_not_awaited()


@pytest.mark.asyncio
async def test_resolve_callback_attachment_target_returns_direct_qpic_url() -> None:
    client = SimpleNamespace(_request_private=AsyncMock())

    target = await resolve_callback_attachment_target(
        client,
        download_url="https://wework.qpic.cn/wwpic/abc.jpg",
        file_name="abc.jpg",
    )

    assert target.url == "https://wework.qpic.cn/wwpic/abc.jpg"
    assert target.requires_object_store_auth is False
    client._request_private.assert_not_awaited()


@pytest.mark.asyncio
async def test_resolve_callback_attachment_target_returns_cdn_c2c_object_url_without_storage() -> None:
    object_url = "http://127.0.0.1:9000/wework/wwcdn/image.jpg"
    client = SimpleNamespace(_request_private=AsyncMock(return_value={"data": {"url": object_url}}))

    target = await resolve_callback_attachment_target(
        client,
        download_url="",
        file_id="306b0201020464abcdef",
        file_name="image.jpg",
        file_size=3,
        aes_key="aes",
        attachment_kind="image",
        is_hd=False,
        base_request={"cdn_dns": "cdn", "client_version": "5.0.0", "corp_id": "corp", "vid": "vid"},
    )

    assert target.url == object_url
    assert target.object_url == object_url
    assert target.bucket is None
    assert target.key is None
    assert target.requires_object_store_auth is True


@pytest.mark.asyncio
async def test_resolve_callback_attachment_target_uses_cdn_download_url_without_storage() -> None:
    object_url = "http://127.0.0.1:9000/wework/wwcdn/file.docx"
    client = SimpleNamespace(
        _request_private=AsyncMock(return_value={"data": {"url": object_url}})
    )

    target = await resolve_callback_attachment_target(
        client,
        download_url="https://imunion.weixin.qq.com/cgi-bin/mmae-bin/tpdownloadmedia?param=abc",
        file_name="file.docx",
        aes_key="aes",
        auth_key="auth",
        base_request={"cdn_dns": "cdn", "client_version": "5.0.0", "corp_id": "corp", "vid": "vid"},
    )

    assert target.url == object_url
    assert target.object_url == object_url
    assert target.bucket is None
    assert target.key is None
    assert target.requires_object_store_auth is True


@pytest.mark.asyncio
async def test_resolve_callback_attachment_target_presigns_private_object_url_with_storage() -> None:
    object_url = "http://127.0.0.1:9000/wework/wwcdn/file.docx"
    client = SimpleNamespace(
        _request_private=AsyncMock(return_value={"data": {"url": object_url}})
    )
    storage = SimpleNamespace(
        config=SimpleNamespace(url_expires_seconds=900),
        parse_object_url=lambda url: ("wework", "wwcdn/file.docx"),
        presign_get_url=lambda bucket, key: f"https://signed.example/{bucket}/{key}?signature=1",
    )
    before = datetime.now(UTC)

    target = await resolve_callback_attachment_target(
        client,
        download_url="https://imunion.weixin.qq.com/cgi-bin/mmae-bin/tpdownloadmedia?param=abc",
        file_name="file.docx",
        aes_key="aes",
        auth_key="auth",
        base_request={"cdn_dns": "cdn", "client_version": "5.0.0", "corp_id": "corp", "vid": "vid"},
        storage=storage,
    )

    assert target.url == "https://signed.example/wework/wwcdn/file.docx?signature=1"
    assert target.object_url == object_url
    assert target.bucket == "wework"
    assert target.key == "wwcdn/file.docx"
    assert target.requires_object_store_auth is False
    assert target.expires_at is not None
    assert before + timedelta(seconds=899) <= target.expires_at <= datetime.now(UTC) + timedelta(seconds=901)


@pytest.mark.asyncio
async def test_resolve_callback_attachment_target_routes_big_file_id() -> None:
    client = SimpleNamespace(
        _request_private=AsyncMock(
            return_value={
                "data": {
                    "url": "https://wwcdn.weixin.qq.com/downloadobject?fileid=*abc",
                }
            }
        )
    )

    target = await resolve_callback_attachment_target(
        client,
        download_url="",
        file_id="*abc",
        file_name="archive.zip",
        file_size=9,
        base_request={"cdn_dns": "cdn", "client_version": "5.0.0", "corp_id": "corp", "vid": "vid"},
    )

    assert target.url == "https://wwcdn.weixin.qq.com/downloadobject?fileid=*abc"
    assert target.headers is None
    client._request_private.assert_awaited_once_with(
        "/cloud/big_download",
        data={
            "url": "*abc",
            "file_name": "archive.zip",
            "file_size": 9,
            "base_request": {"cdn_dns": "cdn", "client_version": "5.0.0", "corp_id": "corp", "vid": "vid"},
        },
    )


@pytest.mark.asyncio
async def test_download_callback_attachment_resolves_private_wecdn_url(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = patch_async_client(monkeypatch, DummyResponse(content=b"docx", headers={"content-type": "application/octet-stream"}))
    client = SimpleNamespace(
        _request_private=AsyncMock(return_value={"data": {"url": "https://wecdn.example/report.docx"}})
    )

    result = await download_callback_attachment(
        client,
        download_url="https://imunion.weixin.qq.com/cgi-bin/mmae-bin/tpdownloadmedia?param=abc",
        file_name="report.docx",
        file_size=4,
        aes_key="aes",
        auth_key="auth",
        base_request={"cdn_dns": "cdn", "client_version": "5.0.0", "corp_id": "corp", "vid": "vid"},
        max_bytes=1024,
    )

    assert result.data == b"docx"
    assert result.file_name == "report.docx"
    assert result.content_type == "application/octet-stream"
    client._request_private.assert_awaited_once_with(
        "/cloud/wx_download",
        data={
            "url": "https://imunion.weixin.qq.com/cgi-bin/mmae-bin/tpdownloadmedia?param=abc",
            "file_name": "report.docx",
            "aes_key": "aes",
            "auth_key": "auth",
            "base_request": {"cdn_dns": "cdn", "client_version": "5.0.0", "corp_id": "corp", "vid": "vid"},
        },
    )
    assert calls["url"] == "https://wecdn.example/report.docx"


@pytest.mark.asyncio
async def test_download_callback_attachment_uses_get_cdn_info_when_base_request_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = patch_async_client(monkeypatch, DummyResponse(content=b"img", headers={"content-type": "image/jpeg"}))
    client = SimpleNamespace(
        _request_private=AsyncMock(return_value={"data": {"url": "https://wecdn.example/image.jpg"}}),
        _request_public=AsyncMock(
            return_value={
                "data": {
                    "cdn_dns": "cdn",
                    "client_version": "5.0.0",
                    "corp_id": "corp",
                    "vid": "vid",
                }
            }
        ),
    )

    result = await download_callback_attachment(
        client,
        download_url="https://imunion.weixin.qq.com/cgi-bin/mmae-bin/tpdownloadmedia?param=abc",
        file_name="image.jpg",
        file_size=3,
        aes_key="aes",
        auth_key="auth",
        max_bytes=1024,
    )

    assert result.data == b"img"
    client._request_public.assert_awaited_once_with("/cdn/get_cdn_info", data={})
    client._request_private.assert_awaited_once_with(
        "/cloud/wx_download",
        data={
            "url": "https://imunion.weixin.qq.com/cgi-bin/mmae-bin/tpdownloadmedia?param=abc",
            "file_name": "image.jpg",
            "aes_key": "aes",
            "auth_key": "auth",
            "base_request": {"cdn_dns": "cdn", "client_version": "5.0.0", "corp_id": "corp", "vid": "vid"},
        },
    )
    assert calls["url"] == "https://wecdn.example/image.jpg"


@pytest.mark.asyncio
async def test_download_callback_attachment_rejects_missing_url() -> None:
    with pytest.raises(QwSaasRequestError, match="download_url or file_id"):
        await download_callback_attachment(SimpleNamespace(), download_url="", file_name="report.pdf")


@pytest.mark.asyncio
async def test_download_callback_attachment_rejects_large_file_before_network(monkeypatch: pytest.MonkeyPatch) -> None:
    client = SimpleNamespace(_request_private=AsyncMock())

    with pytest.raises(QwSaasRequestError, match="exceeds"):
        await download_callback_attachment(
            client,
            download_url="https://files.example/big.zip",
            file_name="big.zip",
            file_size=200,
            max_bytes=100,
        )

    client._request_private.assert_not_awaited()


@pytest.mark.asyncio
async def test_download_callback_attachment_routes_c2c_file_id(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = patch_async_client(monkeypatch, DummyResponse(content=b"img", headers={"content-type": "image/jpeg"}))
    client = SimpleNamespace(
        _request_private=AsyncMock(return_value={"data": {"url": "http://minio.example/wework/wwcdn/image.jpg"}})
    )

    result = await download_callback_attachment(
        client,
        download_url="",
        file_id="306b0201020464abcdef",
        file_name="image.jpg",
        file_size=3,
        aes_key="aes",
        attachment_kind="image",
        is_hd=True,
        base_request={"cdn_dns": "cdn", "client_version": "5.0.0", "corp_id": "corp", "vid": "vid"},
        max_bytes=1024,
    )

    assert result.data == b"img"
    assert result.file_name == "image.jpg"
    client._request_private.assert_awaited_once_with(
        "/cloud/c2c_download",
        data={
            "file_id": "306b0201020464abcdef",
            "file_name": "image.jpg",
            "file_size": 3,
            "file_type": 1,
            "aes_key": "aes",
            "to_mp3": False,
            "base_request": {"cdn_dns": "cdn", "client_version": "5.0.0", "corp_id": "corp", "vid": "vid"},
        },
    )
    assert calls["url"] == "http://minio.example/wework/wwcdn/image.jpg"


@pytest.mark.asyncio
async def test_download_callback_attachment_routes_big_file_id(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = patch_async_client(
        monkeypatch,
        DummyResponse(content=b"zip-bytes", headers={"content-type": "application/zip"}),
    )
    client = SimpleNamespace(
        _request_private=AsyncMock(
            return_value={
                "data": {
                    "url": "https://wwcdn.weixin.qq.com/downloadobject?fileid=*abc&authkey=token",
                }
            }
        )
    )

    result = await download_callback_attachment(
        client,
        download_url="",
        file_id="*abc",
        file_name="archive.zip",
        file_size=9,
        base_request={"cdn_dns": "cdn", "client_version": "5.0.0", "corp_id": "corp", "vid": "vid"},
        max_bytes=1024,
    )

    assert result.data == b"zip-bytes"
    assert result.file_name == "archive.zip"
    client._request_private.assert_awaited_once_with(
        "/cloud/big_download",
        data={
            "url": "*abc",
            "file_name": "archive.zip",
            "file_size": 9,
            "base_request": {"cdn_dns": "cdn", "client_version": "5.0.0", "corp_id": "corp", "vid": "vid"},
        },
    )
    assert calls["url"] == "https://wwcdn.weixin.qq.com/downloadobject?fileid=*abc&authkey=token"
    assert calls["headers"] is None

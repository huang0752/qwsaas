from __future__ import annotations

from typing import Any

import pytest

from qwsaas import QwSaasApiError, QwSaasClient, QwSaasHttpError, QwSaasResponseError
from qwsaas.exceptions import QwSaasRequestError


class DummyResponse:
    def __init__(
        self,
        *,
        status_code: int = 200,
        body: Any = None,
        text: str = "",
        json_error: Exception | None = None,
    ) -> None:
        self.status_code = status_code
        self._body = body if body is not None else {"error_code": 0, "data": {"ok": True}}
        self.text = text or str(self._body)
        self._json_error = json_error

    def json(self) -> Any:
        if self._json_error:
            raise self._json_error
        return self._body


def patch_async_client(monkeypatch: pytest.MonkeyPatch, response: DummyResponse) -> dict[str, Any]:
    calls: dict[str, Any] = {}

    class FakeAsyncClient:
        def __init__(self, *, timeout: float) -> None:
            calls["timeout"] = timeout

        async def __aenter__(self) -> "FakeAsyncClient":
            return self

        async def __aexit__(self, *args: object) -> None:
            return None

        async def post(self, url: str, json: dict[str, Any]) -> DummyResponse:
            calls["url"] = url
            calls["json"] = json
            return response

    monkeypatch.setattr("qwsaas.client.httpx.AsyncClient", FakeAsyncClient)
    return calls


@pytest.mark.asyncio
async def test_public_request_payload_includes_auth_path_and_guid(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = patch_async_client(monkeypatch, DummyResponse())
    client = QwSaasClient(app_key="app", app_secret="secret", guid="guid-1")

    result = await client._request_public("/msg/send_text", {"content": "hello"})

    assert result["data"]["ok"] is True
    assert calls["url"] == "https://chat-api.juhebot.com/open/GuidRequest"
    assert calls["json"] == {
        "app_key": "app",
        "app_secret": "secret",
        "path": "/msg/send_text",
        "data": {"content": "hello", "guid": "guid-1"},
    }


@pytest.mark.asyncio
async def test_request_public_entrypoint_injects_guid(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = patch_async_client(monkeypatch, DummyResponse())
    client = QwSaasClient(app_key="app", app_secret="secret", guid="guid-1")

    await client.request("/msg/send_text", {"content": "hello"})

    assert calls["json"]["path"] == "/msg/send_text"
    assert calls["json"]["data"] == {"content": "hello", "guid": "guid-1"}


@pytest.mark.asyncio
async def test_request_public_entrypoint_defaults_empty_data(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = patch_async_client(monkeypatch, DummyResponse())
    client = QwSaasClient(app_key="app", app_secret="secret", guid="guid-1")

    await client.request("/cdn/get_cdn_info")

    assert calls["json"]["path"] == "/cdn/get_cdn_info"
    assert calls["json"]["data"] == {"guid": "guid-1"}


@pytest.mark.asyncio
async def test_request_public_entrypoint_rejects_non_dict_data() -> None:
    client = QwSaasClient(app_key="app", app_secret="secret", guid="guid-1")

    with pytest.raises(QwSaasRequestError, match="data must be a dict"):
        await client.request("/msg/send_text", ["bad"])  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_private_request_builds_url_from_private_base(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = patch_async_client(monkeypatch, DummyResponse())
    client = QwSaasClient(
        app_key="app",
        app_secret="secret",
        guid="guid-1",
        private_base_url="https://private.example/base/",
    )

    await client._request_private("/cloud/c2c_upload", {"url": "https://file.example/a"})

    assert calls["url"] == "https://private.example/base/cloud/c2c_upload"
    assert calls["json"] == {"url": "https://file.example/a"}


@pytest.mark.asyncio
async def test_request_private_entrypoint_uses_private_base(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = patch_async_client(monkeypatch, DummyResponse())
    client = QwSaasClient(
        app_key="app",
        app_secret="secret",
        guid="guid-1",
        private_base_url="https://private.example",
    )

    await client.request_private("/cloud/wx_download", {"url": "https://imunion.example/file"})

    assert calls["url"] == "https://private.example/cloud/wx_download"
    assert calls["json"] == {"url": "https://imunion.example/file"}


@pytest.mark.asyncio
async def test_public_request_can_override_public_base_url(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = patch_async_client(monkeypatch, DummyResponse())
    client = QwSaasClient(
        app_key="app",
        app_secret="secret",
        guid="guid-1",
        public_base_url="https://juhe.example.test/api/",
    )

    await client._request_public("/msg/send_text", {"content": "hello"})

    assert calls["url"] == "https://juhe.example.test/api/open/GuidRequest"


@pytest.mark.asyncio
async def test_http_status_error_raises_http_error(monkeypatch: pytest.MonkeyPatch) -> None:
    patch_async_client(monkeypatch, DummyResponse(status_code=500, text="server exploded"))
    client = QwSaasClient(app_key="app", app_secret="secret", guid="guid-1")

    with pytest.raises(QwSaasHttpError) as exc_info:
        await client._request_public("/msg/send_text", {})

    assert exc_info.value.status_code == 500


@pytest.mark.asyncio
async def test_invalid_json_response_raises_response_error(monkeypatch: pytest.MonkeyPatch) -> None:
    patch_async_client(
        monkeypatch,
        DummyResponse(text="<html>nope</html>", json_error=ValueError("not json")),
    )
    client = QwSaasClient(app_key="app", app_secret="secret", guid="guid-1")

    with pytest.raises(QwSaasResponseError):
        await client._request_public("/msg/send_text", {})


@pytest.mark.asyncio
async def test_non_zero_error_code_raises_api_error(monkeypatch: pytest.MonkeyPatch) -> None:
    patch_async_client(
        monkeypatch,
        DummyResponse(body={"error_code": 40001, "error_message": "bad auth", "data": {"hint": "x"}}),
    )
    client = QwSaasClient(app_key="app", app_secret="secret", guid="guid-1")

    with pytest.raises(QwSaasApiError) as exc_info:
        await client._request_public("/msg/send_text", {})

    assert exc_info.value.error_code == 40001
    assert exc_info.value.error_message == "bad auth"
    assert exc_info.value.data == {"hint": "x"}


@pytest.mark.asyncio
async def test_base_response_ret_is_treated_as_api_error(monkeypatch: pytest.MonkeyPatch) -> None:
    patch_async_client(
        monkeypatch,
        DummyResponse(body={"baseResponse": {"ret": 100, "errMsg": "ret failed"}}),
    )
    client = QwSaasClient(app_key="app", app_secret="secret", guid="guid-1")

    with pytest.raises(QwSaasApiError) as exc_info:
        await client._request_public("/msg/send_text", {})

    assert exc_info.value.error_code == 100
    assert exc_info.value.error_message == "ret failed"

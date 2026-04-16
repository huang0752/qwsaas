from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

import qwsaas.file_flows as file_flows
from qwsaas.exceptions import QwSaasResponseError


CDN_RESPONSE = {
    "data": {
        "cdn_dns": "cdn",
        "client_version": "5.0.0",
        "corp_id": "corp",
        "vid": "vid",
    }
}


@pytest.mark.asyncio
async def test_small_file_flow_uploads_c2c_and_sends_file(monkeypatch: pytest.MonkeyPatch) -> None:
    client = SimpleNamespace(guid="guid-1")
    monkeypatch.setattr(file_flows, "get_cdn_info", AsyncMock(return_value=CDN_RESPONSE))
    monkeypatch.setattr(
        file_flows,
        "c2c_upload",
        AsyncMock(
            return_value={
                "data": {
                    "file_id": "file-id",
                    "file_size": 12,
                    "file_md5": "md5",
                    "aes_key": "aes",
                }
            }
        ),
    )
    monkeypatch.setattr(file_flows, "send_file", AsyncMock(return_value={"sent": True}))

    result = await file_flows.send_small_file_from_url(
        client,
        conversation_id="S:1001",
        file_url="https://file.example/a.txt",
        file_name="a.txt",
    )

    assert result == {"sent": True}
    file_flows.c2c_upload.assert_awaited_once_with(
        client,
        base_request={
            "cdn_dns": "cdn",
            "client_version": "5.0.0",
            "corp_id": "corp",
            "vid": "vid",
        },
        file_type=5,
        url="https://file.example/a.txt",
    )
    file_flows.send_file.assert_awaited_once_with(
        client,
        conversation_id="S:1001",
        file_id="file-id",
        file_name="a.txt",
        size=12,
        md5="md5",
        aes_key="aes",
    )


@pytest.mark.asyncio
async def test_big_file_flow_uploads_bigcdn_converts_id_and_sends_file(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = SimpleNamespace(guid="guid-1")
    monkeypatch.setattr(file_flows, "get_cdn_info", AsyncMock(return_value=CDN_RESPONSE))
    monkeypatch.setattr(
        file_flows,
        "get_wwfile_auth_key",
        AsyncMock(return_value={"data": {"appid": "1301", "auth_key": "auth"}}),
    )
    monkeypatch.setattr(
        file_flows,
        "big_upload",
        AsyncMock(
            return_value={
                "data": {
                    "file_id": "c2c-file-id",
                    "file_key": "upload-key",
                    "file_size": 1024,
                    "file_md5": "md5",
                }
            }
        ),
    )
    monkeypatch.setattr(
        file_flows,
        "c2c_to_wwfile_id",
        AsyncMock(return_value={"data": {"file_id": "ww-file-id"}}),
    )
    monkeypatch.setattr(file_flows, "send_file", AsyncMock(return_value={"sent": True}))

    result = await file_flows.send_big_file_from_url(
        client,
        conversation_id="R:2001",
        file_url="https://file.example/big.zip",
        file_name="big.zip",
    )

    assert result == {"sent": True}
    file_flows.big_upload.assert_awaited_once()
    file_flows.c2c_to_wwfile_id.assert_awaited_once_with(
        client,
        file_id="c2c-file-id",
        file_md5="md5",
        file_size=1024,
        file_key="upload-key",
    )
    file_flows.send_file.assert_awaited_once_with(
        client,
        conversation_id="R:2001",
        file_id="ww-file-id",
        file_name="big.zip",
        size=1024,
        md5="md5",
    )


@pytest.mark.asyncio
async def test_small_file_flow_requires_cdn_fields(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(file_flows, "get_cdn_info", AsyncMock(return_value={"data": {"vid": "vid"}}))

    with pytest.raises(QwSaasResponseError, match="Missing CDN field"):
        await file_flows.send_small_file_from_url(
            SimpleNamespace(),
            conversation_id="S:1001",
            file_url="https://file.example/a.txt",
            file_name="a.txt",
        )


@pytest.mark.asyncio
async def test_big_file_flow_requires_auth_fields(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(file_flows, "get_cdn_info", AsyncMock(return_value=CDN_RESPONSE))
    monkeypatch.setattr(
        file_flows,
        "get_wwfile_auth_key",
        AsyncMock(return_value={"data": {"appid": "1301"}}),
    )

    with pytest.raises(QwSaasResponseError, match="Missing auth field"):
        await file_flows.send_big_file_from_url(
            SimpleNamespace(guid="guid-1"),
            conversation_id="S:1001",
            file_url="https://file.example/big.zip",
            file_name="big.zip",
        )


@pytest.mark.asyncio
async def test_big_file_flow_requires_big_upload_fields(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(file_flows, "get_cdn_info", AsyncMock(return_value=CDN_RESPONSE))
    monkeypatch.setattr(
        file_flows,
        "get_wwfile_auth_key",
        AsyncMock(return_value={"data": {"appid": "1301", "auth_key": "auth"}}),
    )
    monkeypatch.setattr(file_flows, "big_upload", AsyncMock(return_value={"data": {"file_id": "x"}}))

    with pytest.raises(QwSaasResponseError, match="Missing big upload field"):
        await file_flows.send_big_file_from_url(
            SimpleNamespace(guid="guid-1"),
            conversation_id="S:1001",
            file_url="https://file.example/big.zip",
            file_name="big.zip",
        )


@pytest.mark.asyncio
async def test_big_file_flow_requires_c2c_conversion_fields(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(file_flows, "get_cdn_info", AsyncMock(return_value=CDN_RESPONSE))
    monkeypatch.setattr(
        file_flows,
        "get_wwfile_auth_key",
        AsyncMock(return_value={"data": {"appid": "1301", "auth_key": "auth"}}),
    )
    monkeypatch.setattr(
        file_flows,
        "big_upload",
        AsyncMock(
            return_value={
                "data": {
                    "file_id": "c2c-file-id",
                    "file_key": "upload-key",
                    "file_size": 1024,
                    "file_md5": "md5",
                }
            }
        ),
    )
    monkeypatch.setattr(file_flows, "c2c_to_wwfile_id", AsyncMock(return_value={"data": {}}))

    with pytest.raises(QwSaasResponseError, match="Missing C2C-to-WW field"):
        await file_flows.send_big_file_from_url(
            SimpleNamespace(guid="guid-1"),
            conversation_id="S:1001",
            file_url="https://file.example/big.zip",
            file_name="big.zip",
        )

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

import qwsaas.file_flows as file_flows
from qwsaas.exceptions import QwSaasResponseError, QwSaasStorageConfigError


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


@pytest.mark.asyncio
async def test_send_file_from_url_chooses_small_or_big_by_size_hint(monkeypatch: pytest.MonkeyPatch) -> None:
    client = SimpleNamespace(guid="guid-1")
    monkeypatch.setattr(file_flows, "send_small_file_from_url", AsyncMock(return_value={"small": True}))
    monkeypatch.setattr(file_flows, "send_big_file_from_url", AsyncMock(return_value={"big": True}))

    small = await file_flows.send_file_from_url(
        client,
        "S:1001",
        "https://file.example/small.txt",
        "small.txt",
        size_hint_bytes=file_flows.SMALL_FILE_LIMIT_BYTES,
    )
    big = await file_flows.send_file_from_url(
        client,
        "S:1001",
        "https://file.example/big.zip",
        "big.zip",
        size_hint_bytes=file_flows.SMALL_FILE_LIMIT_BYTES + 1,
    )

    assert small == {"small": True}
    assert big == {"big": True}
    file_flows.send_small_file_from_url.assert_awaited_once_with(
        client,
        conversation_id="S:1001",
        file_url="https://file.example/small.txt",
        file_name="small.txt",
        file_type=5,
    )
    file_flows.send_big_file_from_url.assert_awaited_once_with(
        client,
        conversation_id="S:1001",
        file_url="https://file.example/big.zip",
        file_name="big.zip",
        file_type=5,
    )


@pytest.mark.asyncio
async def test_media_url_helpers_use_expected_file_types(monkeypatch: pytest.MonkeyPatch) -> None:
    client = SimpleNamespace(guid="guid-1")
    monkeypatch.setattr(file_flows, "send_file_from_url", AsyncMock(return_value={"sent": True}))

    await file_flows.send_image_from_url(client, "S:1001", "https://file.example/a.jpg")
    await file_flows.send_video_from_url(client, "S:1001", "https://file.example/a.mp4")
    await file_flows.send_voice_from_url(client, "S:1001", "https://file.example/a.amr")

    assert [call.kwargs["file_type"] for call in file_flows.send_file_from_url.await_args_list] == [2, 4, 5]
    assert [call.kwargs["file_name"] for call in file_flows.send_file_from_url.await_args_list] == [
        "a.jpg",
        "a.mp4",
        "a.amr",
    ]


class FakeStorage:
    def __init__(self) -> None:
        self.deleted: list[tuple[str, str]] = []
        self.uploaded_path: str | None = None

    def upload_file(self, path: str | Path, *, object_key: str | None = None) -> SimpleNamespace:
        self.uploaded_path = str(path)
        return SimpleNamespace(bucket="wework", key="tmp/report.txt", size=5)

    def presign_get_url(self, bucket: str, key: str) -> str:
        return f"https://signed.example/{bucket}/{key}"

    def delete_object(self, bucket: str, key: str) -> None:
        self.deleted.append((bucket, key))


@pytest.mark.asyncio
async def test_send_file_from_path_stages_to_storage_and_cleans_up(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    path = tmp_path / "report.txt"
    path.write_text("hello", encoding="utf-8")
    storage = FakeStorage()
    client = SimpleNamespace(guid="guid-1", storage=storage)
    monkeypatch.setattr(file_flows, "send_file_from_url", AsyncMock(return_value={"sent": True}))

    result = await file_flows.send_file_from_path(client, "S:1001", path)

    assert result == {"sent": True}
    assert storage.uploaded_path == str(path)
    assert storage.deleted == [("wework", "tmp/report.txt")]
    file_flows.send_file_from_url.assert_awaited_once_with(
        client,
        conversation_id="S:1001",
        file_url="https://signed.example/wework/tmp/report.txt",
        file_name="report.txt",
        file_type=5,
        size_hint_bytes=5,
        restage_signed_url=False,
    )


@pytest.mark.asyncio
async def test_send_file_from_path_requires_storage(tmp_path: Path) -> None:
    path = tmp_path / "report.txt"
    path.write_text("hello", encoding="utf-8")

    with pytest.raises(QwSaasStorageConfigError, match="storage"):
        await file_flows.send_file_from_path(SimpleNamespace(guid="guid-1"), "S:1001", path)

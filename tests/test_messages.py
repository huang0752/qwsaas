from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from qwsaas.exceptions import QwSaasRequestError
from qwsaas.messages import send_file, send_text


@pytest.mark.asyncio
async def test_send_text_validates_required_arguments() -> None:
    client = SimpleNamespace(_request_public=AsyncMock())

    with pytest.raises(QwSaasRequestError, match="conversation_id"):
        await send_text(client, "", "hello")

    with pytest.raises(QwSaasRequestError, match="content"):
        await send_text(client, "S:1001", "")


@pytest.mark.asyncio
async def test_send_text_posts_expected_payload() -> None:
    client = SimpleNamespace(_request_public=AsyncMock(return_value={"error_code": 0}))

    result = await send_text(client, "S:1001", "hello")

    assert result == {"error_code": 0}
    client._request_public.assert_awaited_once_with(
        "/msg/send_text",
        data={"conversation_id": "S:1001", "content": "hello"},
    )


@pytest.mark.asyncio
async def test_send_file_validates_required_arguments() -> None:
    client = SimpleNamespace(_request_public=AsyncMock())

    with pytest.raises(QwSaasRequestError, match="file_id"):
        await send_file(client, "S:1001", "", "a.txt", 1, "md5")

    with pytest.raises(QwSaasRequestError, match="file_name"):
        await send_file(client, "S:1001", "file-id", "", 1, "md5")

    with pytest.raises(QwSaasRequestError, match="size"):
        await send_file(client, "S:1001", "file-id", "a.txt", 0, "md5")

    with pytest.raises(QwSaasRequestError, match="md5"):
        await send_file(client, "S:1001", "file-id", "a.txt", 1, "")


@pytest.mark.asyncio
async def test_send_file_includes_optional_aes_key() -> None:
    client = SimpleNamespace(_request_public=AsyncMock(return_value={"error_code": 0}))

    await send_file(client, "S:1001", "file-id", "a.txt", 10, "md5", aes_key="aes")

    client._request_public.assert_awaited_once_with(
        "/msg/send_file",
        data={
            "conversation_id": "S:1001",
            "file_id": "file-id",
            "file_name": "a.txt",
            "size": 10,
            "md5": "md5",
            "aes_key": "aes",
        },
    )

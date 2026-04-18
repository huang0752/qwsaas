from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from qwsaas.exceptions import QwSaasRequestError
from qwsaas.sync import sync_msg, sync_multi_data


@pytest.mark.asyncio
async def test_sync_multi_data_validates_arguments() -> None:
    client = SimpleNamespace(_request_public=AsyncMock())

    with pytest.raises(QwSaasRequestError, match="business_id"):
        await sync_multi_data(client, business_id=0)

    with pytest.raises(QwSaasRequestError, match="limit"):
        await sync_multi_data(client, limit=0)


@pytest.mark.asyncio
async def test_sync_multi_data_posts_expected_payload() -> None:
    client = SimpleNamespace(_request_public=AsyncMock(return_value={"error_code": 0}))

    await sync_multi_data(client, business_id=1, seq="55", limit=5)

    client._request_public.assert_awaited_once_with(
        "/sync/sync_multi_data",
        data={"business_id": 1, "seq": "55", "limit": 5},
    )


@pytest.mark.asyncio
async def test_sync_msg_validates_arguments() -> None:
    client = SimpleNamespace(_request_public=AsyncMock())

    with pytest.raises(QwSaasRequestError, match="sync_key"):
        await sync_msg(client, "")

    with pytest.raises(QwSaasRequestError, match="sync_key"):
        await sync_msg(client, "0")

    with pytest.raises(QwSaasRequestError, match="limit"):
        await sync_msg(client, "1", limit=0)


@pytest.mark.asyncio
async def test_sync_msg_posts_expected_payload() -> None:
    client = SimpleNamespace(_request_public=AsyncMock(return_value={"error_code": 0}))

    await sync_msg(client, "7272648", limit=100)

    client._request_public.assert_awaited_once_with(
        "/sync/sync_msg",
        data={"sync_key": "7272648", "limit": 100},
    )

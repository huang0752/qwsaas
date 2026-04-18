from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from qwsaas.exceptions import QwSaasRequestError
from qwsaas.tags import sync_label_list


@pytest.mark.asyncio
async def test_sync_label_list_validates_sync_type() -> None:
    client = SimpleNamespace(_request_public=AsyncMock())

    with pytest.raises(QwSaasRequestError, match="sync_type"):
        await sync_label_list(client, sync_type=0)


@pytest.mark.asyncio
async def test_sync_label_list_posts_expected_payload() -> None:
    client = SimpleNamespace(_request_public=AsyncMock(return_value={"error_code": 0}))

    await sync_label_list(client, seq="44", sync_type=1)

    client._request_public.assert_awaited_once_with(
        "/label/sync_label_list",
        data={"seq": "44", "sync_type": 1},
    )

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from qwsaas.exceptions import QwSaasRequestError
from qwsaas.rooms import (
    batch_get_member_detail,
    batch_get_room_detail,
    get_room_list,
    sync_room_info,
)


@pytest.mark.asyncio
async def test_get_room_list_validates_paging_arguments() -> None:
    client = SimpleNamespace(_request_public=AsyncMock())

    with pytest.raises(QwSaasRequestError, match="start_index"):
        await get_room_list(client, start_index=-1)

    with pytest.raises(QwSaasRequestError, match="limit"):
        await get_room_list(client, limit=0)


@pytest.mark.asyncio
async def test_get_room_list_posts_expected_payload() -> None:
    client = SimpleNamespace(_request_public=AsyncMock(return_value={"error_code": 0}))

    await get_room_list(client, start_index=10, limit=20)

    client._request_public.assert_awaited_once_with(
        "/room/get_room_list",
        data={"start_index": 10, "limit": 20},
    )


@pytest.mark.asyncio
async def test_batch_get_room_detail_validates_required_arguments() -> None:
    client = SimpleNamespace(_request_public=AsyncMock())

    with pytest.raises(QwSaasRequestError, match="room_list"):
        await batch_get_room_detail(client, [])


@pytest.mark.asyncio
async def test_batch_get_room_detail_posts_expected_payload() -> None:
    client = SimpleNamespace(_request_public=AsyncMock(return_value={"error_code": 0}))

    await batch_get_room_detail(client, ["room-1", "room-2"])

    client._request_public.assert_awaited_once_with(
        "/room/batch_get_room_detail",
        data={"room_list": ["room-1", "room-2"]},
    )


@pytest.mark.asyncio
async def test_batch_get_member_detail_validates_required_arguments() -> None:
    client = SimpleNamespace(_request_public=AsyncMock())

    with pytest.raises(QwSaasRequestError, match="room_id"):
        await batch_get_member_detail(client, "", ["1001"])

    with pytest.raises(QwSaasRequestError, match="user_list"):
        await batch_get_member_detail(client, "room-1", [])


@pytest.mark.asyncio
async def test_batch_get_member_detail_posts_expected_payload() -> None:
    client = SimpleNamespace(_request_public=AsyncMock(return_value={"error_code": 0}))

    await batch_get_member_detail(client, "room-1", ["1001"])

    client._request_public.assert_awaited_once_with(
        "/room/batch_get_member_detail",
        data={"room_id": "room-1", "user_list": ["1001"]},
    )


@pytest.mark.asyncio
async def test_sync_room_info_validates_required_arguments() -> None:
    client = SimpleNamespace(_request_public=AsyncMock())

    with pytest.raises(QwSaasRequestError, match="room_id"):
        await sync_room_info(client, "")

    with pytest.raises(QwSaasRequestError, match="version"):
        await sync_room_info(client, "room-1", version=-1)


@pytest.mark.asyncio
async def test_sync_room_info_posts_expected_payload() -> None:
    client = SimpleNamespace(_request_public=AsyncMock(return_value={"error_code": 0}))

    await sync_room_info(client, "room-1", version=3)

    client._request_public.assert_awaited_once_with(
        "/room/sync_room_info",
        data={"room_id": "room-1", "version": 3},
    )

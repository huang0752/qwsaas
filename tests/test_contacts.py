from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from qwsaas.contacts import batch_get_userinfo, search_contact, sync_contact
from qwsaas.exceptions import QwSaasRequestError


@pytest.mark.asyncio
async def test_sync_contact_validates_limit() -> None:
    client = SimpleNamespace(_request_public=AsyncMock())

    with pytest.raises(QwSaasRequestError, match="limit"):
        await sync_contact(client, limit=0)


@pytest.mark.asyncio
async def test_sync_contact_posts_expected_payload() -> None:
    client = SimpleNamespace(_request_public=AsyncMock(return_value={"error_code": 0}))

    await sync_contact(client, seq="42", limit=20)

    client._request_public.assert_awaited_once_with(
        "/contact/sync_contact",
        data={"seq": "42", "limit": 20},
    )


@pytest.mark.asyncio
async def test_batch_get_userinfo_validates_required_arguments() -> None:
    client = SimpleNamespace(_request_public=AsyncMock())

    with pytest.raises(QwSaasRequestError, match="user_list"):
        await batch_get_userinfo(client, [])


@pytest.mark.asyncio
async def test_batch_get_userinfo_posts_expected_payload() -> None:
    client = SimpleNamespace(_request_public=AsyncMock(return_value={"error_code": 0}))

    await batch_get_userinfo(client, ["1001", "1002"])

    client._request_public.assert_awaited_once_with(
        "/contact/batch_get_userinfo",
        data={"user_list": ["1001", "1002"]},
    )


@pytest.mark.asyncio
async def test_search_contact_validates_required_arguments() -> None:
    client = SimpleNamespace(_request_public=AsyncMock())

    with pytest.raises(QwSaasRequestError, match="keyword"):
        await search_contact(client, "")

    with pytest.raises(QwSaasRequestError, match="type"):
        await search_contact(client, "13800000000", type=0)


@pytest.mark.asyncio
async def test_search_contact_posts_expected_payload() -> None:
    client = SimpleNamespace(_request_public=AsyncMock(return_value={"error_code": 0}))

    await search_contact(client, "13800000000", type=1)

    client._request_public.assert_awaited_once_with(
        "/contact/search_contact",
        data={"keyword": "13800000000", "type": 1},
    )

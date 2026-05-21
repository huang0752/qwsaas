from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from qwsaas.contacts import (
    add_card_contact,
    add_deleted_contact,
    add_search_wx_contact,
    add_search_wx_work_contact,
    add_wx_card_contact,
    agree_contact,
    batch_get_corpinfo,
    batch_get_userinfo,
    delete_contact,
    get_contact_by_qrcode,
    op_black_list,
    search_contact,
    sync_apply_contact,
    sync_contact,
    update_contact,
)
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


@pytest.mark.asyncio
async def test_sync_apply_contact_posts_expected_payload() -> None:
    client = SimpleNamespace(_request_public=AsyncMock(return_value={"ok": True}))

    await sync_apply_contact(client, seq="seq-1", limit=50)

    client._request_public.assert_awaited_once_with(
        "/contact/sync_apply_contact",
        data={"seq": "seq-1", "limit": 50},
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("wrapper", "path"),
    [
        (batch_get_corpinfo, "/contact/batch_get_corpinfo"),
        (update_contact, "/contact/update_contact"),
        (add_search_wx_contact, "/contact/add_search_wx_contact"),
        (add_search_wx_work_contact, "/contact/add_search_wx_work_contact"),
        (add_card_contact, "/contact/add_card_contact"),
        (add_wx_card_contact, "/contact/add_wx_card_contact"),
        (add_deleted_contact, "/contact/add_deleted_contact"),
        (agree_contact, "/contact/agree_contact"),
        (delete_contact, "/contact/delete_contact"),
        (get_contact_by_qrcode, "/contact/get_contact_by_qrcode"),
        (op_black_list, "/contact/op_black_list"),
    ],
)
async def test_contact_payload_wrappers_preserve_payload(wrapper: object, path: str) -> None:
    client = SimpleNamespace(_request_public=AsyncMock(return_value={"ok": True}))

    await wrapper(client, {"user_id": "1001", "extra": "keep"})

    client._request_public.assert_awaited_once_with(
        path,
        data={"user_id": "1001", "extra": "keep"},
    )

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from qwsaas.exceptions import QwSaasRequestError
from qwsaas.rooms import (
    accept_invite_url,
    add_room_contact,
    batch_get_member_detail,
    batch_get_room_detail,
    change_room_master,
    create_empty_outer_room,
    create_inner_room,
    create_outer_room,
    dismiss_room,
    get_room_list,
    get_room_qrcode,
    invite_room_member,
    modify_in_room_nickname,
    modify_invite_status,
    modify_room_admin_flag,
    modify_room_auto_reply,
    modify_room_name,
    modify_room_notice,
    modify_room_remark,
    quit_room,
    remove_room_member,
    room_add_admin,
    room_remove_admin,
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


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("wrapper", "path"),
    [
        (create_outer_room, "/room/create_outer_room"),
        (create_inner_room, "/room/create_inner_room"),
        (create_empty_outer_room, "/room/create_empty_outer_room"),
        (modify_room_name, "/room/modify_room_name"),
        (invite_room_member, "/room/invite_room_member"),
        (remove_room_member, "/room/remove_room_member"),
        (modify_room_notice, "/room/modify_room_notice"),
        (change_room_master, "/room/change_room_master"),
        (room_add_admin, "/room/room_add_admin"),
        (room_remove_admin, "/room/room_remove_admin"),
        (modify_invite_status, "/room/modify_invite_status"),
        (quit_room, "/room/quit_room"),
        (dismiss_room, "/room/dismiss_room"),
        (add_room_contact, "/room/add_room_contact"),
        (accept_invite_url, "/room/accept_invite_url"),
        (modify_in_room_nickname, "/room/modify_in_room_nickname"),
        (modify_room_remark, "/room/modify_room_remark"),
        (get_room_qrcode, "/room/get_room_qrcode"),
        (modify_room_admin_flag, "/room/modify_room_admin_flag"),
        (modify_room_auto_reply, "/room/modify_room_auto_reply"),
    ],
)
async def test_room_payload_wrappers_preserve_payload(wrapper: object, path: str) -> None:
    client = SimpleNamespace(_request_public=AsyncMock(return_value={"ok": True}))

    await wrapper(client, {"room_id": "room-1", "extra": "keep"})

    client._request_public.assert_awaited_once_with(
        path,
        data={"room_id": "room-1", "extra": "keep"},
    )

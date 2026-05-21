from __future__ import annotations

import json
from typing import Any, Awaitable, Callable

import pytest

from qwsaas import (
    batch_get_member_detail,
    batch_get_room_detail,
    batch_get_userinfo,
    get_bind_wxinfo,
    get_cdn_info,
    get_corp_info,
    get_profile,
    get_room_list,
    sync_label_list,
)

from .conftest import (
    build_real_client,
    compact_response,
    first_env,
    require_real_tests,
    target_dm_user_id,
    target_room_id,
)

pytestmark = [pytest.mark.real, pytest.mark.asyncio]


async def test_real_guidrequest_and_common_read_only_wrappers() -> None:
    require_real_tests()
    client = build_real_client()

    cases: list[tuple[str, Callable[[], Awaitable[dict[str, Any]]]]] = [
        ("client.request_get_cdn_info", lambda: client.request("/cdn/get_cdn_info")),
        ("wrapper_get_cdn_info", lambda: get_cdn_info(client)),
        ("get_profile", lambda: get_profile(client)),
        ("get_corp_info", lambda: get_corp_info(client)),
        ("get_bind_wxinfo", lambda: get_bind_wxinfo(client)),
        ("sync_label_list", lambda: sync_label_list(client)),
        ("get_room_list", lambda: get_room_list(client, limit=5)),
    ]

    summaries: dict[str, dict[str, Any]] = {}
    for name, call in cases:
        response = await call()
        assert isinstance(response, dict)
        summaries[name] = compact_response(response)

    print(json.dumps(summaries, ensure_ascii=False, sort_keys=True))


async def test_real_batch_get_authorized_dm_userinfo() -> None:
    require_real_tests()
    client = build_real_client()

    response = await batch_get_userinfo(client, [target_dm_user_id()])

    assert isinstance(response, dict)
    print(json.dumps(compact_response(response), ensure_ascii=False, sort_keys=True))


async def test_real_optional_room_detail() -> None:
    require_real_tests()
    room_id = target_room_id()
    if not room_id:
        pytest.skip("set QWSAAS_TEST_ROOM_ID or QWSAAS_TEST_ROOM_CONVERSATION_ID")

    client = build_real_client()
    detail = await batch_get_room_detail(client, [room_id])
    assert isinstance(detail, dict)

    member_id = first_env("QWSAAS_TEST_ROOM_MEMBER_ID", "JUHE_TEST_ROOM_MEMBER_ID")
    if member_id:
        member_detail = await batch_get_member_detail(client, room_id, [member_id])
        assert isinstance(member_detail, dict)

    print(json.dumps(compact_response(detail), ensure_ascii=False, sort_keys=True))

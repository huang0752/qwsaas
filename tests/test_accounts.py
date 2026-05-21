from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from qwsaas.accounts import (
    get_bind_wxinfo,
    get_corp_info,
    get_profile,
    get_qrcode_card,
    get_qrcode_card_new,
    logout,
)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("wrapper", "path"),
    [
        (get_profile, "/user/get_profile"),
        (get_corp_info, "/user/get_corp_info"),
        (logout, "/user/logout"),
        (get_qrcode_card_new, "/user/get_qrcode_card_new"),
        (get_qrcode_card, "/user/get_qrcode_card"),
        (get_bind_wxinfo, "/user/get_bind_wxinfo"),
    ],
)
async def test_account_wrappers_post_expected_paths(wrapper: object, path: str) -> None:
    client = SimpleNamespace(_request_public=AsyncMock(return_value={"ok": True}))

    await wrapper(client, {"extra": "keep"})

    client._request_public.assert_awaited_once_with(path, data={"extra": "keep"})

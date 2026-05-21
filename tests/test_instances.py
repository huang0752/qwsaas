from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from qwsaas.instances import (
    restore_client,
    set_bridge,
    set_notify_url,
    set_proxy,
    stop_client,
    update_client,
)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("wrapper", "path"),
    [
        (update_client, "/client/update_client"),
        (restore_client, "/client/restore_client"),
        (stop_client, "/client/stop_client"),
        (set_notify_url, "/client/set_notify_url"),
        (set_bridge, "/client/set_bridge"),
        (set_proxy, "/client/set_proxy"),
    ],
)
async def test_instance_wrappers_post_expected_paths(wrapper: object, path: str) -> None:
    client = SimpleNamespace(_request_public=AsyncMock(return_value={"ok": True}))

    await wrapper(client, {"extra": "keep"})

    client._request_public.assert_awaited_once_with(path, data={"extra": "keep"})

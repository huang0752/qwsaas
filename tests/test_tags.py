from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from qwsaas.exceptions import QwSaasRequestError
from qwsaas.tags import contact_add_label, contact_add_labels, create_label, delete_label, modify_label, sync_label_list


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


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("wrapper", "path"),
    [
        (create_label, "/label/create_label"),
        (contact_add_label, "/label/contact_add_label"),
        (delete_label, "/label/delete_label"),
        (modify_label, "/label/modify_label"),
        (contact_add_labels, "/label/contact_add_labels"),
    ],
)
async def test_label_payload_wrappers_preserve_payload(wrapper: object, path: str) -> None:
    client = SimpleNamespace(_request_public=AsyncMock(return_value={"ok": True}))

    await wrapper(client, {"label_id": "label-1", "extra": "keep"})

    client._request_public.assert_awaited_once_with(
        path,
        data={"label_id": "label-1", "extra": "keep"},
    )

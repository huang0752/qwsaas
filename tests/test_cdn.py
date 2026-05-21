from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from qwsaas.cdn import get_cdn_file
from qwsaas.exceptions import QwSaasRequestError


@pytest.mark.asyncio
async def test_get_cdn_file_preserves_payload_fields() -> None:
    client = SimpleNamespace(_request_public=AsyncMock(return_value={"ok": True}))

    await get_cdn_file(client, {"file_id": "file-1", "optional": "keep"})

    client._request_public.assert_awaited_once_with(
        "/cdn/get_cdn_file",
        data={"file_id": "file-1", "optional": "keep"},
    )


@pytest.mark.asyncio
async def test_get_cdn_file_rejects_non_mapping_payload() -> None:
    client = SimpleNamespace(_request_public=AsyncMock())

    with pytest.raises(QwSaasRequestError, match="payload"):
        await get_cdn_file(client, ["bad"])  # type: ignore[arg-type]

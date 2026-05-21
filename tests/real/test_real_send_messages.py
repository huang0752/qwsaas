from __future__ import annotations

import base64
from datetime import datetime, timezone
import json

import pytest

from qwsaas import send_file_from_path, send_image_from_path, send_text

from .conftest import (
    build_real_client,
    build_real_storage,
    compact_response,
    require_real_send_tests,
    target_dm_conversation_id,
)

pytestmark = [pytest.mark.real, pytest.mark.asyncio]

PNG_1X1 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/p9sAAAAASUVORK5CYII="
)


async def test_real_send_text_to_authorized_dm_user() -> None:
    require_real_send_tests()
    client = build_real_client()
    marker = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    response = await send_text(
        client,
        target_dm_conversation_id(),
        f"qwsaas v0.3.0 real text smoke {marker}",
    )

    assert isinstance(response, dict)
    print(json.dumps(compact_response(response), ensure_ascii=False, sort_keys=True))


async def test_real_send_file_to_authorized_dm_user(tmp_path) -> None:
    require_real_send_tests()
    storage = build_real_storage()
    client = build_real_client(storage=storage)
    marker = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = tmp_path / "qwsaas-v0.3.0-real-file.txt"
    path.write_text(f"qwsaas v0.3.0 real file smoke {marker}\n", encoding="utf-8")

    response = await send_file_from_path(client, target_dm_conversation_id(), path, cleanup=True)

    assert isinstance(response, dict)
    print(json.dumps(compact_response(response), ensure_ascii=False, sort_keys=True))


async def test_real_send_image_to_authorized_dm_user(tmp_path) -> None:
    require_real_send_tests()
    storage = build_real_storage()
    client = build_real_client(storage=storage)
    marker = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = tmp_path / f"qwsaas-v0.3.0-real-image-{marker}.png"
    path.write_bytes(base64.b64decode(PNG_1X1))

    response = await send_image_from_path(client, target_dm_conversation_id(), path, cleanup=True)

    assert isinstance(response, dict)
    print(json.dumps(compact_response(response), ensure_ascii=False, sort_keys=True))

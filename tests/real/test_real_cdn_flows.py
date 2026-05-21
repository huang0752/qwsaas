from __future__ import annotations

from datetime import datetime, timezone
import json

import pytest

from qwsaas import c2c_upload, get_cdn_info

from .conftest import build_real_client, build_real_storage, compact_response, require_real_tests

pytestmark = [pytest.mark.real, pytest.mark.asyncio]


async def test_real_c2c_upload_small_file_from_storage_url(tmp_path) -> None:
    require_real_tests()
    storage = build_real_storage()
    client = build_real_client(storage=storage)

    cdn_info = await get_cdn_info(client)
    data = cdn_info.get("data") if isinstance(cdn_info.get("data"), dict) else {}
    base_request = {key: data[key] for key in ("cdn_dns", "client_version", "corp_id", "vid")}

    path = tmp_path / "qwsaas-v0.3.0-real-c2c.txt"
    path.write_text(
        f"qwsaas v0.3.0 c2c smoke {datetime.now(timezone.utc).isoformat()}\n",
        encoding="utf-8",
    )

    stored = None
    try:
        stored = storage.upload_file(path)
        signed_url = storage.presign_get_url(stored.bucket, stored.key, expires_seconds=600)
        response = await c2c_upload(client, base_request=base_request, file_type=5, url=signed_url)
    finally:
        if stored is not None:
            storage.delete_object(stored.bucket, stored.key)

    response_data = response.get("data") if isinstance(response.get("data"), dict) else {}
    assert {"file_id", "file_size", "file_md5", "aes_key"}.issubset(response_data)
    print(json.dumps(compact_response(response), ensure_ascii=False, sort_keys=True))

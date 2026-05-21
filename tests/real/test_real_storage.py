from __future__ import annotations

from datetime import datetime, timezone

import httpx
import pytest

from .conftest import build_real_storage, require_real_tests

pytestmark = pytest.mark.real


def test_real_storage_upload_presign_download_delete(tmp_path) -> None:
    require_real_tests()
    storage = build_real_storage()
    payload = f"qwsaas v0.3.0 storage smoke {datetime.now(timezone.utc).isoformat()}\n".encode()
    path = tmp_path / "qwsaas-v0.3.0-real-storage.txt"
    path.write_bytes(payload)

    stored = None
    try:
        stored = storage.upload_file(path)
        signed_url = storage.presign_get_url(stored.bucket, stored.key, expires_seconds=300)
        response = httpx.get(signed_url, timeout=20, follow_redirects=True)
        response.raise_for_status()

        assert stored.key.startswith(storage.config.prefix.strip("/") + "/")
        assert response.content == payload
    finally:
        if stored is not None:
            storage.delete_object(stored.bucket, stored.key)

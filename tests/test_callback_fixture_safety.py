from __future__ import annotations

import json
from pathlib import Path

import pytest

from qwsaas.callback_fixture_safety import scan_fixture_paths


def write_fixture(root: Path, payload: dict) -> Path:
    directory = root / "real_callbacks"
    directory.mkdir()
    path = directory / "sample.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_fully_redacted_real_fixture_passes(tmp_path: Path) -> None:
    path = write_fixture(
        tmp_path,
        {
            "sender": "CONTACT_A",
            "receiver": "ACCOUNT_A",
            "roomid": "0",
            "sender_name": "REDACTED",
            "aes_key": "REDACTED",
            "base_request": {"authorization": "REDACTED"},
            "url": "https://example.invalid/media?token=REDACTED",
        },
    )
    assert scan_fixture_paths([path]) == []


@pytest.mark.parametrize(
    ("payload", "reason"),
    [
        ({"aes_key": "real-key"}, "sensitive_value"),
        ({"auth_cookies": "session=real"}, "sensitive_value"),
        ({"headers": {"Authorization": "Bearer real"}}, "sensitive_value"),
        ({"url": "https://example.invalid/a?signature=real"}, "url_query_value"),
        ({"sender": "168123456789"}, "real_id_pattern"),
        ({"sender_name": "张三"}, "identity_not_placeholder"),
        ({"sendername": "张三"}, "identity_not_placeholder"),
        ({"base_request": {"auth_key": "real"}}, "sensitive_value"),
        ({"url": "https://evil.example/a"}, "unapproved_host"),
        ({"opaque": "A1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6"}, "high_entropy_string"),
    ],
)
def test_scanner_rejects_secret_or_identity_leaks(tmp_path: Path, payload: dict, reason: str) -> None:
    findings = scan_fixture_paths([write_fixture(tmp_path, payload)])
    assert reason in {item.reason for item in findings}


def test_apifox_public_examples_have_separate_identity_policy() -> None:
    fixture_dir = Path(__file__).parent / "fixtures" / "apifox"
    assert scan_fixture_paths([fixture_dir]) == []

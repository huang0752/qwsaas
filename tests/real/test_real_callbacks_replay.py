from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from qwsaas import MessageRelation, parse_callback_envelope

pytestmark = pytest.mark.real


def _load_callback_payload() -> dict:
    raw_json = os.environ.get("QWSAAS_REAL_CALLBACK_JSON", "").strip()
    if raw_json:
        payload = json.loads(raw_json)
        assert isinstance(payload, dict)
        return payload

    file_path = os.environ.get("QWSAAS_REAL_CALLBACK_FILE", "").strip()
    if file_path:
        payload = json.loads(Path(file_path).read_text(encoding="utf-8"))
        assert isinstance(payload, dict)
        return payload

    pytest.skip("set QWSAAS_REAL_CALLBACK_JSON or QWSAAS_REAL_CALLBACK_FILE")


def test_real_callback_payload_replay_preserves_message_fields() -> None:
    payload = _load_callback_payload()
    parsed = parse_callback_envelope(payload)

    assert parsed.raw_envelope == payload
    assert parsed.messages

    summary = {
        "notify_type": parsed.notify_type,
        "message_count": len(parsed.messages),
        "original_count": sum(
            1 for message in parsed.messages
            if message.message_relation is MessageRelation.ORIGINAL
        ),
        "attachment_count": sum(len(message.attachments) for message in parsed.messages),
        "message_types": sorted(
            {int(message.message_kind) for message in parsed.messages if message.message_kind is not None}
        ),
    }
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))

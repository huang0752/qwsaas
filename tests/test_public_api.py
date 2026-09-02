from __future__ import annotations

from dataclasses import fields
from importlib.metadata import version

import qwsaas


def test_v040_rc_public_api_does_not_export_v035_callback_fields() -> None:
    assert version("qwsaas") == "0.4.0rc1"
    field_names = {item.name for item in fields(qwsaas.JuheCallbackMessage)}
    assert "message_id" not in field_names
    assert "conversation_id" not in field_names
    assert "is_self_echo" not in field_names


def test_v040_exports_callback_contract() -> None:
    expected = {
        "logical_message_key",
        "normalize_callback_identity",
        "parse_and_normalize_callback",
        "parse_callback_envelope",
        "parse_protocol_message",
        "parse_sent_message_ref",
        "parse_sync_messages",
        "try_parse_callback_envelope",
    }
    assert expected <= set(qwsaas.__all__)
    assert {"has_message_flag", "is_original_message", "is_quote_message"}.isdisjoint(qwsaas.__all__)

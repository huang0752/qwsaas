from __future__ import annotations

import json
from pathlib import Path

from qwsaas.callback_messages import parse_protocol_message
from qwsaas.callback_models import (
    LogicalMessageKeyFailure,
    LogicalMessageKeySource,
    MessageSource,
)
from qwsaas.message_results import (
    appinfo_values_equivalent,
    logical_message_key,
    parse_sent_message_ref,
    sent_message_matches_callback,
)


def message(**overrides):
    raw = {
        "id": "LOCAL",
        "seq": "SEQ",
        "appinfo": "GLOBAL",
        "sender": "CONTACT_A",
        "receiver": "ACCOUNT_A",
        "roomid": "0",
        "sendtime": 1700000000,
        "referid": "0",
        "flag": 0,
        "msg_type": 2,
        "content": '{"msg":"hello"}',
    }
    raw.update(overrides)
    return parse_protocol_message(
        raw,
        source=MessageSource.REALTIME_11010,
        source_event_key="EVENT_A",
        item_index=0,
    )


def test_logical_message_key_priority_and_scope() -> None:
    global_key = logical_message_key(message())
    local_a = logical_message_key(message(appinfo=None), current_account_id="A")
    local_b = logical_message_key(message(appinfo=None), current_account_id="B")
    sequence = logical_message_key(message(appinfo=None, id=None), current_account_id="A")

    assert global_key.source is LogicalMessageKeySource.APPINFO
    assert local_a.source is LogicalMessageKeySource.ACCOUNT_ID
    assert sequence.source is LogicalMessageKeySource.ACCOUNT_SEQUENCE
    assert local_a.value != local_b.value
    assert all(result.failure_reason is None for result in (global_key, local_a, sequence))


def test_global_key_needs_no_account_and_is_stable() -> None:
    first = logical_message_key(message())
    second = logical_message_key(message(), current_account_id="OTHER")
    assert first.value == second.value
    assert first.value is not None and "GLOBAL" not in first.value


def test_local_identifier_requires_valid_account() -> None:
    missing = logical_message_key(message(appinfo=None), current_account_id=None)
    invalid = logical_message_key(message(appinfo=None), current_account_id=True)
    assert missing.failure_reason is LogicalMessageKeyFailure.CURRENT_ACCOUNT_REQUIRED
    assert invalid.failure_reason is LogicalMessageKeyFailure.CURRENT_ACCOUNT_INVALID


def test_no_documented_identifier_has_typed_failure_not_fingerprint_fallback() -> None:
    result = logical_message_key(message(appinfo=None, id=None, seq=None), current_account_id="A")
    assert result.value is None
    assert result.source is None
    assert result.failure_reason is LogicalMessageKeyFailure.IDENTIFIERS_MISSING


def test_missing_identifiers_are_reported_before_missing_account() -> None:
    result = logical_message_key(message(appinfo=None, id=None, seq=None))
    assert result.failure_reason is LogicalMessageKeyFailure.IDENTIFIERS_MISSING


def test_invalid_documented_identifiers_are_distinguished() -> None:
    result = logical_message_key(message(appinfo=True, id=1.5, seq=False), current_account_id="A")
    assert result.failure_reason is LogicalMessageKeyFailure.IDENTIFIERS_INVALID


def test_parse_only_documented_data_msg_data() -> None:
    response = {
        "error_code": 0,
        "data": {
            "msg_data": {
                "id": "LOCAL",
                "seq": "SEQ",
                "appinfo": "GLOBAL",
                "sender": "ACCOUNT_A",
                "receiver": "CONTACT_A",
                "roomid": "0",
                "sendtime": 1700000000,
                "flag": 0,
                "asid": "ASID_A",
            }
        },
    }
    parsed = parse_sent_message_ref(response)
    assert parsed is not None
    assert parsed.appinfo == "GLOBAL"
    assert parse_sent_message_ref({"msg_data": response["data"]["msg_data"]}) is None


def test_strong_sent_callback_match_requires_equal_valid_appinfo() -> None:
    sent = parse_sent_message_ref({"data": {"msg_data": {"appinfo": "GLOBAL"}}})
    assert sent is not None
    assert sent_message_matches_callback(sent, message()) is True
    assert sent_message_matches_callback(sent, message(appinfo="OTHER")) is False
    assert sent_message_matches_callback(sent, message(appinfo=None)) is False


def test_appinfo_equivalence_accepts_raw_and_strict_base64_forms() -> None:
    raw = "CAU_APPINFO_A"
    encoded = "Q0FVX0FQUElORk9fQQ=="

    assert appinfo_values_equivalent(encoded, raw) is True
    assert appinfo_values_equivalent(raw, encoded) is True
    assert appinfo_values_equivalent(raw, raw) is True
    assert appinfo_values_equivalent(encoded, encoded) is True


def test_appinfo_equivalence_rejects_invalid_or_ambiguous_base64_without_raising() -> None:
    assert appinfo_values_equivalent("Q0FV====", "CAU") is False
    assert appinfo_values_equivalent("//4=", "��") is False
    assert appinfo_values_equivalent(True, "True") is False
    assert appinfo_values_equivalent(None, "None") is False


def test_sent_callback_match_keeps_raw_appinfo_and_never_uses_text_or_time() -> None:
    encoded = "Q0FVX0FQUElORk9fQQ=="
    response = {
        "data": {
            "msg_data": {
                "id": "LOCAL_A",
                "seq": "SEQ_A",
                "appinfo": encoded,
                "sendtime": 1700000000,
            }
        }
    }
    sent = parse_sent_message_ref(response)
    assert sent is not None

    callback = message(appinfo="CAU_APPINFO_A", sendtime=1700000000, content="same")
    assert sent_message_matches_callback(sent, callback) is True
    assert sent.appinfo == encoded
    assert response["data"]["msg_data"]["appinfo"] == encoded

    unrelated = message(appinfo="CAU_APPINFO_B", sendtime=1700000000, content="same")
    assert sent_message_matches_callback(sent, unrelated) is False


def test_invalid_msg_data_returns_none() -> None:
    assert parse_sent_message_ref({"data": {"msg_data": "bad"}}) is None


def test_apifox_documented_msg_data_response_shapes_parse() -> None:
    fixture_dir = Path(__file__).parent / "fixtures" / "apifox"
    for name in ("send_text_response.json", "send_image_response.json", "report_unread_response.json"):
        response = json.loads((fixture_dir / name).read_text(encoding="utf-8"))
        parsed = parse_sent_message_ref(response)
        assert parsed is not None
        assert parsed.appinfo


def test_apifox_send_text_example_preserves_documented_appinfo_form() -> None:
    fixture = Path(__file__).parent / "fixtures" / "apifox" / "send_text_response.json"
    response = json.loads(fixture.read_text(encoding="utf-8"))
    parsed = parse_sent_message_ref(response)

    assert parsed is not None
    assert parsed.id == "1066172"
    assert parsed.seq == "7272187"
    assert parsed.appinfo == "Q0FVUW5ldVRzQVlZOGNiTHIrNkN0ZUFYSUkyOXBjb0w="
    assert appinfo_values_equivalent(
        parsed.appinfo,
        "CAUQneuTsAYY8cbLr+6CteAXII29pcoL",
    )


def test_sanitized_real_outbound_callback_structure_correlates() -> None:
    fixture = Path(__file__).parent / "fixtures" / "correlation" / "outbound_appinfo.json"
    payload = json.loads(fixture.read_text(encoding="utf-8"))
    sent = parse_sent_message_ref(payload["sent_response"])

    assert sent is not None
    assert sent.id == "LOCAL_A"
    assert sent.seq == "SEQ_A"
    assert sent_message_matches_callback(sent, message(**payload["callback"]["data"])) is True

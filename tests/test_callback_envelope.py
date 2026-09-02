from __future__ import annotations

import json
from pathlib import Path

import pytest

from qwsaas.callback_models import MessageSource
from qwsaas.callbacks import parse_callback_envelope, try_parse_callback_envelope
from qwsaas.exceptions import CallbackParseErrorCode, QwSaasCallbackParseError

FIXTURES = Path(__file__).parent / "fixtures" / "apifox"


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_official_top_level_11010_parses_one_message() -> None:
    payload = load_fixture("notify_11010.json")
    parsed = parse_callback_envelope(payload)

    assert parsed.notify_type == 11010
    assert len(parsed.messages) == 1
    assert parsed.messages[0].source is MessageSource.REALTIME_11010
    assert parsed.raw_event == payload


@pytest.mark.parametrize(
    "fixture",
    ["notify_11002.json", "notify_11003.json", "notify_11004.json", "notify_11011.json", "notify_2166.json"],
)
def test_non_message_documented_callbacks_preserve_raw_without_messages(fixture: str) -> None:
    payload = load_fixture(fixture)
    parsed = parse_callback_envelope(payload)

    assert parsed.messages == ()
    assert parsed.raw_event == payload


def test_top_level_notify_type_is_authoritative_and_strict() -> None:
    payload = {
        "notify_type": "11010",
        "event": {"notify_type": 11010, "data": {}},
    }
    with pytest.raises(QwSaasCallbackParseError) as exc:
        parse_callback_envelope(payload)
    assert exc.value.code is CallbackParseErrorCode.INVALID_NOTIFY_TYPE


def test_sdk_event_object_and_string_wrappers_are_supported() -> None:
    event = load_fixture("notify_11010.json")
    object_parsed = parse_callback_envelope({"type": "callback", "event_id": "one", "event": event})
    string_parsed = parse_callback_envelope({"type": "callback", "event_id": "two", "event": json.dumps(event)})

    assert object_parsed.wrapper_event_id == "one"
    assert string_parsed.wrapper_event_id == "two"
    assert len(object_parsed.messages) == len(string_parsed.messages) == 1


def test_wrapper_event_id_scopes_envelope_fingerprint() -> None:
    event = load_fixture("notify_11010.json")
    first = parse_callback_envelope({"event_id": "WRAPPER_A", "event": event})
    replay = parse_callback_envelope({"event_id": "WRAPPER_A", "event": event})
    other = parse_callback_envelope({"event_id": "WRAPPER_B", "event": event})

    assert first.envelope_event_key == replay.envelope_event_key
    assert first.envelope_event_key != other.envelope_event_key


def test_confirmed_data_wrapper_is_supported() -> None:
    event = load_fixture("notify_11010.json")
    parsed = parse_callback_envelope({"type": "callback", "event_id": "one", "data": event})
    assert parsed.raw_event == event


def test_conflicting_wrapper_events_are_rejected() -> None:
    with pytest.raises(QwSaasCallbackParseError) as exc:
        parse_callback_envelope(
            {
                "event": {"notify_type": 11002, "data": {}},
                "data": {"notify_type": 11003, "data": {}},
            }
        )
    assert exc.value.code is CallbackParseErrorCode.CONFLICTING_EVENTS


def test_try_parser_returns_none_for_invalid_structure() -> None:
    assert try_parse_callback_envelope({}) is None


def test_unverified_11013_shape_is_rejected_in_rc() -> None:
    with pytest.raises(QwSaasCallbackParseError) as exc:
        parse_callback_envelope({"guid": "x", "notify_type": 11013, "data": []})
    assert exc.value.code is CallbackParseErrorCode.UNVERIFIED_BATCH_SHAPE

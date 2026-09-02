from __future__ import annotations

import pytest

from qwsaas.callback_models import MessageSource
from qwsaas.callback_sync import parse_sync_messages


def record(message_id: str) -> dict:
    return {
        "id": message_id,
        "seq": message_id,
        "appinfo": f"APP_{message_id}",
        "sender": "CONTACT_A",
        "receiver": "ACCOUNT_A",
        "roomid": "0",
        "sendtime": 1700000000,
        "referid": "0",
        "flag": 0,
        "msg_type": 2,
        "content": '{"msg":"hello"}',
    }


def test_sync_parses_explicit_records_without_callback_envelope() -> None:
    messages = parse_sync_messages([record("1"), record("2")], sync_page_key="PAGE_A")
    assert [item.source for item in messages] == [MessageSource.SYNC_MSG, MessageSource.SYNC_MSG]
    assert [item.batch_index for item in messages] == [0, 1]
    assert messages[0].callback_message_key != messages[1].callback_message_key
    assert all(item.raw_event == {} for item in messages)


def test_sync_replay_keys_are_stable() -> None:
    first = parse_sync_messages([record("1")], sync_page_key="PAGE_A")
    second = parse_sync_messages([record("1")], sync_page_key="PAGE_A")
    assert first[0].callback_message_key == second[0].callback_message_key


def test_sync_does_not_guess_records_from_response_envelope() -> None:
    with pytest.raises(TypeError):
        parse_sync_messages({"data": [record("1")]}, sync_page_key="PAGE_A")


def test_sync_rejects_non_mapping_item() -> None:
    with pytest.raises(TypeError):
        parse_sync_messages([record("1"), "bad"], sync_page_key="PAGE_A")

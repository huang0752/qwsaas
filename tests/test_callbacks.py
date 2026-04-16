from __future__ import annotations

import json

from qwsaas.callbacks import NOTIFY_BATCH_NEW_MESSAGE, NOTIFY_NEW_MESSAGE, parse_callback_envelope


def test_parse_single_stringified_callback_message() -> None:
    parsed = parse_callback_envelope(
        {
            "type": "callback",
            "event_id": "evt-1",
            "event": json.dumps(
                {
                    "guid": "guid-1",
                    "notify_type": NOTIFY_NEW_MESSAGE,
                    "data": {
                        "msg_type": 2,
                        "content": '{"msg":"hello"}',
                        "sender": "1001",
                        "sender_name": "Alice",
                        "msg_id": "msg-1",
                    },
                }
            ),
        }
    )

    assert parsed is not None
    assert parsed.event_id == "evt-1"
    assert parsed.guid == "guid-1"
    assert parsed.notify_type == NOTIFY_NEW_MESSAGE
    assert len(parsed.messages) == 1
    message = parsed.messages[0]
    assert message.message_id == "msg-1"
    assert message.message_type == 2
    assert message.text == "hello"
    assert message.sender_id == "1001"
    assert message.sender_name == "Alice"
    assert message.conversation_id == "S:1001"
    assert message.is_group is False


def test_parse_batch_group_callback_messages() -> None:
    parsed = parse_callback_envelope(
        {
            "type": "callback",
            "event_id": "evt-2",
            "data": {
                "guid": "guid-1",
                "notify_type": NOTIFY_BATCH_NEW_MESSAGE,
                "data": [
                    {
                        "msg_type": 2,
                        "content": "hello",
                        "sender": "1001",
                        "roomid": "2001",
                        "at_list": "bot,ops",
                        "msg_id": "msg-1",
                    },
                    {
                        "msg_type": 5,
                        "content": '{"data":{"image":{"url":"https://example.test/a.jpg"}}}',
                        "sender": "1002",
                        "roomid": "2001",
                        "msg_id": "msg-2",
                    },
                ],
            },
        }
    )

    assert parsed is not None
    assert len(parsed.messages) == 2
    assert parsed.messages[0].conversation_id == "R:2001"
    assert parsed.messages[0].at_list == ("bot", "ops")
    assert parsed.messages[1].message_type == 5
    assert parsed.messages[1].text == ""


def test_parse_callback_envelope_returns_none_for_empty_or_malformed_payload() -> None:
    assert parse_callback_envelope({}) is None
    assert parse_callback_envelope({"type": "callback", "event": ""}) is None
    assert parse_callback_envelope({"type": "callback", "event": "not-json"}) is None


def test_parse_callback_marks_self_echo() -> None:
    parsed = parse_callback_envelope(
        {
            "type": "callback",
            "event": {
                "guid": "guid-1",
                "notify_type": NOTIFY_NEW_MESSAGE,
                "data": {
                    "msg_type": 2,
                    "content": "bot echo",
                    "sender": "1688858038755018",
                    "roomid": "2001",
                    "send_flag": 1,
                    "id": "juhe-id-1",
                },
            },
        }
    )

    assert parsed is not None
    assert parsed.messages[0].is_self_echo is True

from __future__ import annotations

from qwsaas.callback_messages import parse_protocol_message
from qwsaas.callback_models import (
    CallbackParseIssueCode,
    MessageRelation,
    MessageSource,
    MessageStateKind,
)
from qwsaas.enums import MessageFlagField, MsgType


def raw_message(**overrides: object) -> dict:
    value = {
        "id": "local-1",
        "seq": "sequence-1",
        "appinfo": "global-1",
        "sender": "account-1",
        "receiver": "contact-1",
        "roomid": "0",
        "sendtime": 1711649467,
        "sender_name": "Example",
        "content_type": 2,
        "referid": "0",
        "flag": 0,
        "content": "hello",
        "at_list": [],
        "quote_content": "",
        "quote_appinfo": "",
        "send_flag": 1,
        "msg_type": 2,
        "asid": "0",
    }
    value.update(overrides)
    return value


def parse(raw: dict, *, source: MessageSource = MessageSource.REALTIME_11010, index: int = 0):
    return parse_protocol_message(raw, source=source, source_event_key="event-key", item_index=index)


def test_parse_documented_text_message_fields() -> None:
    message = parse(raw_message())

    assert message.protocol.id == "local-1"
    assert message.protocol.receiver == "contact-1"
    assert message.message_kind is MsgType.MsgTypeText
    assert message.message_relation is MessageRelation.ORIGINAL
    assert message.state_kinds == frozenset({MessageStateKind.UNKNOWN})
    assert message.sent_at is not None
    assert message.sent_at.tzinfo is not None


def test_unknown_and_missing_message_types_do_not_default_to_text() -> None:
    unknown = parse(raw_message(msg_type=999))
    missing = parse(raw_message(msg_type=None))
    string_number = parse(raw_message(msg_type="2"))
    float_number = parse(raw_message(msg_type=2.0))

    assert unknown.message_kind is None
    assert missing.message_kind is None
    assert string_number.message_kind is None
    assert float_number.message_kind is None
    assert CallbackParseIssueCode.UNKNOWN_MESSAGE_TYPE in {item.code for item in unknown.parse_issues}
    assert CallbackParseIssueCode.INVALID_FIELD in {item.code for item in missing.parse_issues}


def test_system_message_with_referid_or_revoke_flag_is_not_revoke() -> None:
    message = parse(
        raw_message(
            msg_type=1011,
            referid="123",
            flag=int(MessageFlagField.MessageFlagFieldRevoke),
        )
    )

    assert message.message_kind is MsgType.MsgTypeSystem
    assert MessageStateKind.REVOKE not in message.state_kinds
    assert message.message_relation is MessageRelation.SUBSIDIARY


def test_revoke_and_read_signals_are_additive() -> None:
    message = parse(
        raw_message(
            msg_type=1,
            referid="123",
            flag=int(MessageFlagField.MessageFlagFieldHasRead | MessageFlagField.MessageFlagFieldRevoke),
        )
    )

    assert MessageStateKind.REVOKE in message.state_kinds
    assert MessageStateKind.READ in message.state_kinds


def test_missing_or_invalid_referid_has_unknown_relation() -> None:
    assert parse(raw_message(referid=None)).message_relation is MessageRelation.UNKNOWN
    assert parse(raw_message(referid=True)).message_relation is MessageRelation.UNKNOWN


def test_batch_item_fingerprints_are_distinct_and_replay_stable() -> None:
    raw = raw_message()
    first = parse(raw, source=MessageSource.REALTIME_11013, index=0)
    second = parse(raw, source=MessageSource.REALTIME_11013, index=1)
    replay = parse(raw, source=MessageSource.REALTIME_11013, index=0)

    assert first.callback_message_key != second.callback_message_key
    assert first.callback_message_key == replay.callback_message_key


def test_unknown_flag_bits_are_preserved() -> None:
    message = parse(raw_message(flag=1 << 30))
    assert message.unknown_flag_bits == 1 << 30
    assert CallbackParseIssueCode.UNKNOWN_FLAG_BITS in {item.code for item in message.parse_issues}


def test_composite_revoke_by_ack_flag_is_recognized_without_unknown_bits() -> None:
    message = parse(raw_message(flag=int(MessageFlagField.MessageFlagFieldRevokeByAck)))
    assert MessageFlagField.MessageFlagFieldRevokeByAck in message.flags
    assert MessageStateKind.REVOKE in message.state_kinds
    assert message.unknown_flag_bits == 0

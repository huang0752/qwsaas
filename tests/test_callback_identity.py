from __future__ import annotations

import pytest

from qwsaas.callback_identity import (
    normalize_account_id,
    normalize_callback_identity,
    normalize_room_id,
    normalize_user_id,
)
from qwsaas.callback_messages import parse_protocol_message
from qwsaas.callback_models import (
    ConversationKind,
    IdentityFailureReason,
    MessageDirection,
    MessageSource,
)


def message(**overrides):
    raw = {
        "id": "10",
        "seq": "11",
        "appinfo": "APP_A",
        "sender": "CONTACT_A",
        "receiver": "ACCOUNT_A",
        "roomid": "0",
        "sendtime": 1700000000,
        "referid": "0",
        "flag": 0,
        "send_flag": 0,
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


@pytest.mark.parametrize(
    ("normalizer", "value", "expected"),
    [
        (normalize_account_id, " S:001 ", "001"),
        (normalize_user_id, 123, "123"),
        (normalize_room_id, "R:ROOM_A", "ROOM_A"),
        (normalize_user_id, "0", None),
        (normalize_user_id, "S:0", None),
        (normalize_room_id, "R:0", None),
        (normalize_room_id, 0.0, None),
        (normalize_account_id, True, None),
        (normalize_user_id, 1.0, None),
        (normalize_user_id, "R:ROOM_A", None),
        (normalize_user_id, "s:USER_A", None),
        (normalize_user_id, "S:S:USER_A", None),
        (normalize_room_id, "R:R:ROOM_A", None),
    ],
)
def test_id_normalization_is_strict(normalizer, value, expected) -> None:
    assert normalizer(value) == expected


def test_private_inbound_and_outbound_share_peer_conversation() -> None:
    inbound = normalize_callback_identity(message(), current_account_id="ACCOUNT_A")
    outbound = normalize_callback_identity(
        message(sender="ACCOUNT_A", receiver="CONTACT_A", send_flag=1),
        current_account_id="S:ACCOUNT_A",
    )

    for normalized in (inbound, outbound):
        assert normalized.conversation_kind is ConversationKind.DIRECT
        assert normalized.contact_id == "CONTACT_A"
        assert normalized.provider_conversation_id == "S:CONTACT_A"
        assert normalized.account_conversation_key == "juhe:ACCOUNT_A:S:CONTACT_A"
        assert normalized.identity_failures == frozenset()
    assert inbound.direction is MessageDirection.INBOUND
    assert inbound.is_self_authored is False
    assert outbound.direction is MessageDirection.OUTBOUND
    assert outbound.is_self_authored is True


@pytest.mark.parametrize("is_group", ["0", "false", 0, False])
def test_boolean_like_group_hints_do_not_override_zero_roomid(is_group: object) -> None:
    normalized = normalize_callback_identity(
        message(is_group=is_group, is_chatroom_msg=is_group),
        current_account_id="ACCOUNT_A",
    )
    assert normalized.conversation_kind is ConversationKind.DIRECT
    assert normalized.provider_conversation_id == "S:CONTACT_A"


def test_private_conversation_does_not_fall_back_to_sender() -> None:
    normalized = normalize_callback_identity(message(receiver="SOMEONE_ELSE"), current_account_id="ACCOUNT_A")

    assert normalized.conversation_kind is ConversationKind.UNKNOWN
    assert normalized.direction is MessageDirection.UNKNOWN
    assert normalized.provider_conversation_id is None
    assert normalized.account_conversation_key is None
    assert IdentityFailureReason.ACCOUNT_NOT_PARTICIPANT in normalized.identity_failures
    assert normalized.is_self_authored is None


def test_private_message_with_no_distinct_peer_reports_peer_missing() -> None:
    normalized = normalize_callback_identity(
        message(sender="ACCOUNT_A", receiver="ACCOUNT_A"),
        current_account_id="ACCOUNT_A",
    )
    assert IdentityFailureReason.DIRECT_PEER_MISSING in normalized.identity_failures
    assert IdentityFailureReason.ACCOUNT_NOT_PARTICIPANT not in normalized.identity_failures


def test_missing_current_account_has_explicit_failure() -> None:
    normalized = normalize_callback_identity(message(), current_account_id=None)
    assert normalized.direction is MessageDirection.UNKNOWN
    assert normalized.provider_conversation_id is None
    assert IdentityFailureReason.CURRENT_ACCOUNT_MISSING in normalized.identity_failures


def test_invalid_ids_have_field_specific_failures() -> None:
    normalized = normalize_callback_identity(
        message(sender=True, receiver="R:WRONG"),
        current_account_id="S:S:BROKEN",
    )
    assert normalized.identity_failures >= {
        IdentityFailureReason.CURRENT_ACCOUNT_INVALID,
        IdentityFailureReason.SENDER_INVALID,
        IdentityFailureReason.RECEIVER_INVALID,
    }


def test_room_target_is_known_but_direction_is_release_gated() -> None:
    normalized = normalize_callback_identity(
        message(sender="CONTACT_A", receiver="ROOM_A", roomid="R:ROOM_A"),
        current_account_id="ACCOUNT_A",
    )
    assert normalized.conversation_kind is ConversationKind.ROOM
    assert normalized.room_id == "ROOM_A"
    assert normalized.provider_conversation_id == "R:ROOM_A"
    assert normalized.account_conversation_key == "juhe:ACCOUNT_A:R:ROOM_A"
    assert normalized.direction is MessageDirection.UNKNOWN
    assert normalized.is_self_authored is None
    assert normalized.identity_failures == {IdentityFailureReason.ROOM_DIRECTION_UNVERIFIED}


def test_normalize_envelope_keeps_protocol_parsing_independent() -> None:
    from qwsaas import parse_callback_envelope

    parsed = parse_callback_envelope(
        {"guid": "G", "notify_type": 11010, "data": message().raw_message}
    )
    normalized = normalize_callback_identity(parsed, current_account_id="ACCOUNT_A")
    assert normalized.source is parsed
    assert normalized.messages[0].provider_conversation_id == "S:CONTACT_A"

from __future__ import annotations

from dataclasses import fields

from qwsaas.callback_models import (
    ConversationKind,
    IdentityFailureReason,
    JuheCallbackMessage,
    MessageDirection,
    MessageRelation,
)
from qwsaas.enums import MsgType


def test_callback_model_is_breaking_and_tristate_contract_is_explicit() -> None:
    names = {item.name for item in fields(JuheCallbackMessage)}
    assert "protocol" in names
    assert "callback_message_key" in names
    assert "attachments" in names
    assert "message_id" not in names
    assert "conversation_id" not in names
    assert "is_self_echo" not in names
    assert MessageDirection.UNKNOWN.value == "unknown"
    assert ConversationKind.ROOM.value == "room"
    assert MessageRelation.UNKNOWN.value == "unknown"
    assert IdentityFailureReason.ROOM_DIRECTION_UNVERIFIED.value == "room_direction_unverified"


def test_documented_message_type_values_remain_exact() -> None:
    assert MsgType.MsgTypeRevoke == 1
    assert MsgType.MsgTypeSystem == 1011
    assert MsgType.MsgTypeReadReport == 1012

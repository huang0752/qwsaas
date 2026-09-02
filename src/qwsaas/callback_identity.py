from __future__ import annotations

from enum import StrEnum
from typing import Any, overload

from .callback_models import (
    ConversationKind,
    IdentityFailureReason,
    JuheCallbackEnvelope,
    JuheCallbackMessage,
    JuheNormalizedCallbackEnvelope,
    JuheNormalizedCallbackMessage,
    MessageDirection,
)


class _IdStatus(StrEnum):
    VALID = "valid"
    MISSING = "missing"
    INVALID = "invalid"


def normalize_account_id(value: object) -> str | None:
    return _normalize_id(value, allowed_prefix="S:")[0]


def normalize_user_id(value: object) -> str | None:
    return _normalize_id(value, allowed_prefix="S:")[0]


def normalize_room_id(value: object) -> str | None:
    return _normalize_id(value, allowed_prefix="R:")[0]


@overload
def normalize_callback_identity(
    source: JuheCallbackMessage,
    *,
    current_account_id: object,
) -> JuheNormalizedCallbackMessage: ...


@overload
def normalize_callback_identity(
    source: JuheCallbackEnvelope,
    *,
    current_account_id: object,
) -> JuheNormalizedCallbackEnvelope: ...


def normalize_callback_identity(
    source: JuheCallbackMessage | JuheCallbackEnvelope,
    *,
    current_account_id: object,
) -> JuheNormalizedCallbackMessage | JuheNormalizedCallbackEnvelope:
    """Apply account-scoped identity without reparsing protocol data."""
    if isinstance(source, JuheCallbackEnvelope):
        return JuheNormalizedCallbackEnvelope(
            source=source,
            messages=tuple(
                _normalize_message(item, current_account_id=current_account_id)
                for item in source.messages
            ),
        )
    if isinstance(source, JuheCallbackMessage):
        return _normalize_message(source, current_account_id=current_account_id)
    raise TypeError("source must be JuheCallbackMessage or JuheCallbackEnvelope")


def _normalize_message(
    source: JuheCallbackMessage,
    *,
    current_account_id: object,
) -> JuheNormalizedCallbackMessage:
    protocol = source.protocol
    account, account_status = _normalize_id(current_account_id, allowed_prefix="S:")
    sender, sender_status = _normalize_id(protocol.sender, allowed_prefix="S:")
    receiver, receiver_status = _normalize_id(protocol.receiver, allowed_prefix="S:")
    room, room_status = _normalize_id(protocol.roomid, allowed_prefix="R:")
    failures: set[IdentityFailureReason] = set()

    _record_status(
        account_status,
        failures,
        missing=IdentityFailureReason.CURRENT_ACCOUNT_MISSING,
        invalid=IdentityFailureReason.CURRENT_ACCOUNT_INVALID,
    )
    if sender_status is _IdStatus.INVALID:
        failures.add(IdentityFailureReason.SENDER_INVALID)
    if receiver_status is _IdStatus.INVALID:
        failures.add(IdentityFailureReason.RECEIVER_INVALID)
    if room_status is _IdStatus.INVALID:
        failures.add(IdentityFailureReason.ROOM_ID_INVALID)

    kind = ConversationKind.UNKNOWN
    direction = MessageDirection.UNKNOWN
    contact = None
    provider_key = None
    if room_status is _IdStatus.VALID:
        kind = ConversationKind.ROOM
        provider_key = f"R:{room}"
        failures.add(IdentityFailureReason.ROOM_DIRECTION_UNVERIFIED)
    elif room_status is not _IdStatus.INVALID and account is not None:
        if sender == account and receiver is not None and receiver != account:
            kind = ConversationKind.DIRECT
            direction = MessageDirection.OUTBOUND
            contact = receiver
        elif receiver == account and sender is not None and sender != account:
            kind = ConversationKind.DIRECT
            direction = MessageDirection.INBOUND
            contact = sender
        elif sender == account and receiver == account:
            failures.add(IdentityFailureReason.DIRECT_PEER_MISSING)
        elif sender_status is _IdStatus.VALID and receiver_status is _IdStatus.VALID:
            failures.add(IdentityFailureReason.ACCOUNT_NOT_PARTICIPANT)
        else:
            failures.add(IdentityFailureReason.DIRECT_PEER_MISSING)
        if contact is not None:
            provider_key = f"S:{contact}"
    elif room_status is not _IdStatus.INVALID:
        failures.add(IdentityFailureReason.DIRECT_PEER_MISSING)

    account_key = f"juhe:{account}:{provider_key}" if account and provider_key else None
    return JuheNormalizedCallbackMessage(
        source=source,
        sender_id=sender,
        receiver_id=receiver,
        room_id=room,
        current_account_id=account,
        conversation_kind=kind,
        direction=direction,
        contact_id=contact,
        provider_conversation_id=provider_key,
        account_conversation_key=account_key,
        identity_failures=frozenset(failures),
    )


def _normalize_id(value: Any, *, allowed_prefix: str) -> tuple[str | None, _IdStatus]:
    if value is None:
        return None, _IdStatus.MISSING
    if isinstance(value, bool):
        return None, _IdStatus.INVALID
    if isinstance(value, int):
        if value == 0:
            return None, _IdStatus.MISSING
        if value > 0:
            return str(value), _IdStatus.VALID
        return None, _IdStatus.INVALID
    if isinstance(value, float):
        return (None, _IdStatus.MISSING) if value == 0.0 else (None, _IdStatus.INVALID)
    if not isinstance(value, str):
        return None, _IdStatus.INVALID

    text = value.strip()
    if not text or text.lower() in {"0", "0.0", "null", "none"}:
        return None, _IdStatus.MISSING
    if text[:2].lower() in {"s:", "r:"} and not text.startswith(allowed_prefix):
        return None, _IdStatus.INVALID
    if text.startswith(allowed_prefix):
        text = text[len(allowed_prefix) :]
        if not text or text[:2].lower() in {"s:", "r:"}:
            return None, _IdStatus.INVALID
        if text.lower() in {"0", "0.0", "null", "none"}:
            return None, _IdStatus.MISSING
    return text, _IdStatus.VALID


def _record_status(
    status: _IdStatus,
    failures: set[IdentityFailureReason],
    *,
    missing: IdentityFailureReason,
    invalid: IdentityFailureReason,
) -> None:
    if status is _IdStatus.MISSING:
        failures.add(missing)
    elif status is _IdStatus.INVALID:
        failures.add(invalid)

from __future__ import annotations

import base64
import binascii
import hashlib
from collections.abc import Mapping
from enum import StrEnum
from typing import Any

from .callback_identity import normalize_account_id
from .callback_models import (
    JuheCallbackMessage,
    JuheLogicalMessageKey,
    JuheMessageProtocolFields,
    JuheSentMessageRef,
    LogicalMessageKeyFailure,
    LogicalMessageKeySource,
    ProtocolIdValue,
)


class _ValueStatus(StrEnum):
    VALID = "valid"
    MISSING = "missing"
    INVALID = "invalid"


def logical_message_key(
    message: JuheCallbackMessage | JuheMessageProtocolFields,
    *,
    current_account_id: object | None = None,
) -> JuheLogicalMessageKey:
    """Build a durable logical key only from documented provider identifiers."""
    protocol = message.protocol if isinstance(message, JuheCallbackMessage) else message
    if not isinstance(protocol, JuheMessageProtocolFields):
        raise TypeError("message must be JuheCallbackMessage or JuheMessageProtocolFields")

    appinfo, appinfo_status = _identifier(protocol.appinfo)
    if appinfo is not None:
        return _key("global", "appinfo", appinfo, LogicalMessageKeySource.APPINFO)

    local_id, id_status = _identifier(protocol.id)
    sequence, seq_status = _identifier(protocol.seq)
    if local_id is None and sequence is None:
        statuses = (appinfo_status, id_status, seq_status)
        failure = (
            LogicalMessageKeyFailure.IDENTIFIERS_INVALID
            if _ValueStatus.INVALID in statuses
            else LogicalMessageKeyFailure.IDENTIFIERS_MISSING
        )
        return JuheLogicalMessageKey(value=None, source=None, failure_reason=failure)

    account = normalize_account_id(current_account_id)
    if account is None:
        account_status = _account_status(current_account_id)
        failure = (
            LogicalMessageKeyFailure.CURRENT_ACCOUNT_REQUIRED
            if account_status is _ValueStatus.MISSING
            else LogicalMessageKeyFailure.CURRENT_ACCOUNT_INVALID
        )
        return JuheLogicalMessageKey(value=None, source=None, failure_reason=failure)

    if local_id is not None:
        return _key(account, "id", local_id, LogicalMessageKeySource.ACCOUNT_ID)
    if sequence is not None:
        return _key(account, "seq", sequence, LogicalMessageKeySource.ACCOUNT_SEQUENCE)
    raise AssertionError("validated local identifier unexpectedly missing")


def parse_sent_message_ref(response: Mapping[str, Any]) -> JuheSentMessageRef | None:
    """Extract only the documented data.msg_data send-result record."""
    if not isinstance(response, Mapping):
        return None
    data = response.get("data")
    if not isinstance(data, Mapping):
        return None
    raw = data.get("msg_data")
    if not isinstance(raw, Mapping):
        return None
    return JuheSentMessageRef(
        id=raw.get("id"),
        seq=raw.get("seq"),
        appinfo=raw.get("appinfo"),
        sender=raw.get("sender"),
        receiver=raw.get("receiver"),
        roomid=raw.get("roomid"),
        sendtime=_optional_int(raw.get("sendtime")),
        flag=_optional_int(raw.get("flag")),
        asid=raw.get("asid"),
    )


def sent_message_matches_callback(
    sent: JuheSentMessageRef,
    callback: JuheCallbackMessage | JuheMessageProtocolFields,
) -> bool:
    """Return a strong match only for equivalent, valid global appinfo values."""
    protocol = callback.protocol if isinstance(callback, JuheCallbackMessage) else callback
    return appinfo_values_equivalent(sent.appinfo, protocol.appinfo)


def appinfo_values_equivalent(left: ProtocolIdValue, right: ProtocolIdValue) -> bool:
    """Compare raw appinfo values and their strict Base64 UTF-8 candidates.

    The original values remain untouched. Each side is decoded at most once, and
    only canonical standard Base64 with valid UTF-8 contributes a candidate.
    """
    left_candidates = _appinfo_candidates(left)
    right_candidates = _appinfo_candidates(right)
    return bool(left_candidates and left_candidates.intersection(right_candidates))


def _key(
    scope: str,
    kind: str,
    identifier: str,
    source: LogicalMessageKeySource,
) -> JuheLogicalMessageKey:
    raw = (
        f"juhe-message/global/{kind}/{identifier}"
        if scope == "global"
        else f"juhe-message/account/{scope}/{kind}/{identifier}"
    )
    return JuheLogicalMessageKey(
        value=hashlib.sha256(raw.encode("utf-8")).hexdigest(),
        source=source,
        failure_reason=None,
    )


def _identifier(value: Any) -> tuple[str | None, _ValueStatus]:
    if value is None:
        return None, _ValueStatus.MISSING
    if isinstance(value, bool):
        return None, _ValueStatus.INVALID
    if isinstance(value, int):
        if value == 0:
            return None, _ValueStatus.MISSING
        if value > 0:
            return str(value), _ValueStatus.VALID
        return None, _ValueStatus.INVALID
    if isinstance(value, float):
        return (None, _ValueStatus.MISSING) if value == 0.0 else (None, _ValueStatus.INVALID)
    if not isinstance(value, str):
        return None, _ValueStatus.INVALID
    text = value.strip()
    if not text or text.lower() in {"0", "0.0", "null", "none"}:
        return None, _ValueStatus.MISSING
    return text, _ValueStatus.VALID


def _appinfo_candidates(value: ProtocolIdValue) -> frozenset[str]:
    original, _ = _identifier(value)
    if original is None:
        return frozenset()

    candidates = {original}
    if not isinstance(value, str):
        return frozenset(candidates)

    try:
        encoded = original.encode("ascii")
        decoded_bytes = base64.b64decode(encoded, validate=True)
        if base64.b64encode(decoded_bytes) != encoded:
            return frozenset(candidates)
        decoded = decoded_bytes.decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError, binascii.Error, ValueError):
        return frozenset(candidates)

    decoded_identifier, _ = _identifier(decoded)
    if decoded_identifier is not None:
        candidates.add(decoded_identifier)
    return frozenset(candidates)


def _account_status(value: Any) -> _ValueStatus:
    _, status = _identifier(value)
    if status is not _ValueStatus.VALID:
        return status
    return _ValueStatus.INVALID if normalize_account_id(value) is None else _ValueStatus.VALID


def _optional_int(value: Any) -> int | None:
    return int(value) if isinstance(value, int) and not isinstance(value, bool) else None

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from .callback_identity import normalize_callback_identity
from .callback_messages import canonical_sha256, parse_protocol_message
from .callback_models import (
    JuheCallbackEnvelope,
    JuheNormalizedCallbackEnvelope,
    MessageSource,
)
from .enums import NotifyType
from .exceptions import CallbackParseErrorCode, QwSaasCallbackParseError

NOTIFY_NEW_MESSAGE = int(NotifyType.NotifyTypeNewMsg)
NOTIFY_BATCH_NEW_MESSAGE = int(NotifyType.NotifyTypeBatchNewMsg)


def parse_callback_envelope(payload: Mapping[str, Any]) -> JuheCallbackEnvelope:
    """Parse a real-time callback without applying account identity context."""
    if not isinstance(payload, Mapping):
        raise _error(CallbackParseErrorCode.INVALID_INPUT_TYPE, "$")

    envelope = dict(payload)
    event, event_path = _select_event(envelope)
    notify_type = _strict_notify_type(event.get("notify_type"), f"{event_path}.notify_type")
    wrapper_event_id = _optional_text(envelope.get("event_id"))
    guid = _optional_text(event.get("guid"))
    event_key = canonical_sha256(
        {"guid": guid, "wrapper_event_id": wrapper_event_id}
        if wrapper_event_id is not None
        else {"guid": guid, "notify_type": notify_type, "data": event.get("data")}
    )
    messages = ()
    if notify_type == NOTIFY_NEW_MESSAGE:
        raw_message = event.get("data")
        if not isinstance(raw_message, Mapping):
            raise _error(
                CallbackParseErrorCode.INVALID_MESSAGE_PAYLOAD,
                f"{event_path}.data",
                notify_type,
            )
        messages = (
            parse_protocol_message(
                raw_message,
                source=MessageSource.REALTIME_11010,
                source_event_key=event_key,
                item_index=0,
                raw_event=event,
            ),
        )
    elif notify_type == NOTIFY_BATCH_NEW_MESSAGE:
        # Apifox documents the enum but not its payload shape. RC builds fail
        # closed until a complete, sanitized real callback becomes a fixture.
        raise _error(
            CallbackParseErrorCode.UNVERIFIED_BATCH_SHAPE,
            f"{event_path}.data",
            notify_type,
        )

    return JuheCallbackEnvelope(
        wrapper_event_id=wrapper_event_id,
        guid=guid,
        notify_type=notify_type,
        notify_type_name=notify_type_name(notify_type),
        envelope_event_key=event_key,
        messages=messages,
        parse_issues=(),
        raw_event=event,
        raw_envelope=envelope,
    )


def try_parse_callback_envelope(payload: Mapping[str, Any]) -> JuheCallbackEnvelope | None:
    try:
        return parse_callback_envelope(payload)
    except QwSaasCallbackParseError:
        return None


def parse_and_normalize_callback(
    payload: Mapping[str, Any],
    *,
    current_account_id: object,
) -> JuheNormalizedCallbackEnvelope:
    parsed = parse_callback_envelope(payload)
    normalized = normalize_callback_identity(parsed, current_account_id=current_account_id)
    assert isinstance(normalized, JuheNormalizedCallbackEnvelope)
    return normalized


def notify_type_name(value: NotifyType | int) -> str:
    try:
        return NotifyType(int(value)).name
    except (TypeError, ValueError):
        return str(value)


def _select_event(envelope: dict[str, Any]) -> tuple[dict[str, Any], str]:
    # The documented top-level form is authoritative, including if malformed.
    if "notify_type" in envelope:
        return envelope, "$"

    candidates: list[tuple[dict[str, Any], str]] = []
    for key in ("event", "data"):
        if key not in envelope:
            continue
        event = _coerce_event(envelope[key], f"$.{key}")
        if event is not None and "notify_type" in event:
            candidates.append((event, f"$.{key}"))

    if not candidates:
        raise _error(CallbackParseErrorCode.MISSING_NOTIFY_TYPE, "$.notify_type")
    first_event, first_path = candidates[0]
    if any(event != first_event for event, _ in candidates[1:]):
        raise _error(CallbackParseErrorCode.CONFLICTING_EVENTS, "$")
    return first_event, first_path


def _coerce_event(value: Any, path: str) -> dict[str, Any] | None:
    if isinstance(value, Mapping):
        return dict(value)
    if isinstance(value, str):
        try:
            decoded = json.loads(value)
        except (TypeError, ValueError):
            raise _error(CallbackParseErrorCode.INVALID_EVENT, path) from None
        if isinstance(decoded, Mapping):
            return dict(decoded)
        raise _error(CallbackParseErrorCode.INVALID_EVENT, path)
    if value is None:
        return None
    raise _error(CallbackParseErrorCode.INVALID_EVENT, path)


def _strict_notify_type(value: Any, path: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise _error(CallbackParseErrorCode.INVALID_NOTIFY_TYPE, path)
    return int(value)


def _optional_text(value: Any) -> str | None:
    if value is None or isinstance(value, bool):
        return None
    text = str(value).strip()
    return text or None


def _error(
    code: CallbackParseErrorCode,
    path: str,
    notify_type: int | None = None,
) -> QwSaasCallbackParseError:
    return QwSaasCallbackParseError(code, path=path, notify_type=notify_type)

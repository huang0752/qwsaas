from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class JuheApiResponse:
    """Normalized Juhe API response envelope."""

    error_code: int
    error_message: str
    data: Any
    raw: dict[str, Any]


@dataclass(frozen=True)
class JuheCallbackMessage:
    """Normalized callback message without Hermes-specific runtime semantics."""

    message_id: str
    message_type: int
    text: str
    sender_id: str | None
    sender_name: str | None
    conversation_id: str | None
    at_list: tuple[str, ...]
    is_group: bool
    is_self_echo: bool
    raw_message: dict[str, Any]
    raw_event: dict[str, Any]


@dataclass(frozen=True)
class JuheCallbackEnvelope:
    """Normalized callback envelope that may contain one or more messages."""

    event_id: str | None
    guid: str | None
    notify_type: int
    messages: tuple[JuheCallbackMessage, ...]
    raw_event: dict[str, Any]
    raw_envelope: dict[str, Any]

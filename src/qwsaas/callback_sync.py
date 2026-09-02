from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from .callback_messages import canonical_sha256, parse_protocol_message
from .callback_models import JuheCallbackMessage, MessageSource


def parse_sync_messages(
    raw_messages: Sequence[Mapping[str, Any]],
    *,
    sync_page_key: str,
) -> tuple[JuheCallbackMessage, ...]:
    """Parse caller-extracted /sync/sync_msg records without inventing 11013."""
    if isinstance(raw_messages, (str, bytes, bytearray, Mapping)) or not isinstance(
        raw_messages, Sequence
    ):
        raise TypeError("raw_messages must be an explicit sequence of mappings")
    if not isinstance(sync_page_key, str) or not sync_page_key.strip():
        raise ValueError("sync_page_key must be a non-empty string")

    page_fingerprint = canonical_sha256({"sync_page_key": sync_page_key})
    parsed: list[JuheCallbackMessage] = []
    for index, raw_message in enumerate(raw_messages):
        if not isinstance(raw_message, Mapping):
            raise TypeError(f"raw_messages[{index}] must be a mapping")
        parsed.append(
            parse_protocol_message(
                raw_message,
                source=MessageSource.SYNC_MSG,
                source_event_key=page_fingerprint,
                item_index=index,
            )
        )
    return tuple(parsed)

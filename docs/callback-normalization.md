# Callback normalization

## Two-stage API

```python
from qwsaas import normalize_callback_identity, parse_callback_envelope

protocol = parse_callback_envelope(payload)
normalized = normalize_callback_identity(protocol, current_account_id=account_id)
```

Parsing is deterministic for a payload and does not depend on an account cache. Identity can be applied later without reparsing raw data. `parse_and_normalize_callback()` is the composition shortcut.

## Private identity

After strict ID normalization:

- `sender == current_account_id` means outbound and the peer is `receiver`.
- `receiver == current_account_id` means inbound and the peer is `sender`.
- Otherwise direction and conversation are unknown with a typed failure.

Both directions produce `provider_conversation_id = S:<peer>` and `account_conversation_key = juhe:<account>:S:<peer>`.

A non-zero room ID produces `R:<room>` and `juhe:<account>:R:<room>`. Room direction stays unknown with `ROOM_DIRECTION_UNVERIFIED` until the real device/API matrix establishes it. A host may add its tenant, connection, or instance namespace around `account_conversation_key`; qwsaas does not guess that namespace.

## Safe diagnostics

Callback models use a redacted repr. `to_safe_dict()` returns types, counts, state, and issue codes without IDs, message content, names, filenames, URLs, cookies, keys, base requests, or raw payloads. Raw values remain explicitly available to protocol consumers and must not be logged directly.

Messages expose `message_relation`, additive `state_kinds`, and `attachments`. `is_self_authored` is a derived `bool | None`; there is no echo-discard flag.

## Sync records

Callers must extract the message-record sequence from their verified `/sync/sync_msg` response and pass it explicitly:

```python
messages = parse_sync_messages(records, sync_page_key=page_cursor_or_capture_id)
```

The helper does not guess response-envelope layout or synthesize a callback notify type.

# Callback protocol boundary

This document records only behavior established by the current [Juhe/QW SaaS documentation](https://wework.apifox.cn/). Real observations extend the contract only after a complete callback is sanitized, reviewed, and added to the regression matrix.

## Documented facts

- The official callback envelope has top-level `guid`, integer `notify_type`, and `data`.
- `11010` is a new-message callback. `11013` is named as a batch-new-message enum, but its payload shape is not documented.
- Message `id` and `seq` are unique only within a user/account scope. `appinfo` is globally unique.
- `referid == 0` identifies an original message; a non-zero value identifies a changed subsidiary record.
- `MsgTypeRevoke == 1`, `MsgTypeSystem == 1011`, and `MsgTypeReadReport == 1012`.
- Private provider targets use `S:<user-id>` and room targets use `R:<room-id>`.

The public examples contain `receiver` and `send_flag`, but do not fully define their semantics across inbound, desktop, mobile, API, and room traffic. The SDK preserves them without inventing meaning.

## Dispatch contract

`parse_callback_envelope()` accepts the official top-level form plus observed SDK wrappers containing an object or JSON-string `event`, and the confirmed `data` wrapper. A top-level `notify_type` is authoritative: if present but invalid, parsing fails instead of falling through to nested data.

Only 11010 currently creates a message. Known and unknown non-message notify types return an envelope with `messages=()`. RC builds reject 11013 with `UNVERIFIED_BATCH_SHAPE`; `/sync/sync_msg` records use `parse_sync_messages()` and are never converted into 11013.

Raw protocol fields are preserved in `JuheMessageProtocolFields`. Strict parsing does not coerce string or floating-point message types into integers, and unknown types remain unknown rather than becoming text.

## Identifier boundary

`envelope_event_key` and `callback_message_key` are payload fingerprints useful for exact replay diagnostics. They are not persistent business-message identifiers. Use `logical_message_key()`, which chooses `appinfo`, then account-scoped `id`, then account-scoped `seq`.

Outbound response correlation is strong only when `parse_sent_message_ref()` finds a valid `data.msg_data.appinfo` equivalent to the callback's `appinfo`. The official [send-text response](https://wework.apifox.cn/api-276644016) shows a canonical Base64-looking value, while the official [11010 callback](https://wework.apifox.cn/doc-7013959) shows a raw value; sanitized observed traffic separately proves that a sent value can decode exactly to its callback value. `appinfo_values_equivalent()` therefore intersects each original value with at most one canonical standard-Base64, strict-UTF-8 decoded candidate. It does not mutate or replace the raw values. Invalid Base64 and invalid UTF-8 add no decoded candidate and do not raise. `send_flag`, timestamps, text, `id`, or `seq` alone do not prove an API echo.

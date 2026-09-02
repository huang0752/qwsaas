# Migrating callback consumers from v0.3 to v0.4

This is a breaking upgrade. No v0.3.5 aliases are retained.

| Removed v0.3 field/helper | v0.4 contract |
| --- | --- |
| `message_id` | `protocol.appinfo`, `protocol.id`, `protocol.seq`, or `logical_message_key()` |
| `conversation_id` | identity-normalized `provider_conversation_id` |
| application-global bare conversation | `account_conversation_key`; host adds its own connection namespace |
| `is_group` | `conversation_kind` |
| `is_self_echo` | `direction` and tri-state `is_self_authored`; explicit `appinfo` correlation for API sends |
| `is_original_message()` | `message_relation is MessageRelation.ORIGINAL` |
| `has_message_flag()` | membership in `message.flags` or `message.state_kinds` |
| one attachment on message | `message.attachments` tuple |

Replace one-stage callback handling with parse then identity normalization. Handle `QwSaasCallbackParseError` for malformed envelopes, and do not treat `try_parse_callback_envelope() == None` as a valid non-message event.

Sync recovery must call `parse_sync_messages()` on explicit records. Do not wrap sync responses in synthetic 11013 events.

This SDK change does not migrate Super Mate data, merge previously split conversations, or preserve old fields. Those are separate host migrations after the RC protocol matrix is accepted.

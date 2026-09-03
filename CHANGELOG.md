# Changelog

## 0.4.0rc2

- Fixed outbound callback correlation when a send response carries canonical Base64 UTF-8 `appinfo` while the callback carries its decoded value.
- Added public `appinfo_values_equivalent()` candidate matching without replacing either audited raw value.
- Kept correlation limited to `appinfo`; message text, timestamps, `send_flag`, `id`, and `seq` are not fallback match keys.
- Added the official send-text response representation and a sanitized observed send/callback pair as regression fixtures.

## 0.4.0rc1

- Replaced the v0.3 callback model with separate protocol parsing and account-scoped identity normalization.
- Added strict official-envelope dispatch: only 11010 creates a message; non-message events preserve raw data with zero messages.
- Added distinct envelope and per-item callback fingerprints, plus durable logical keys based on `appinfo` or account-scoped `id`/`seq`.
- Added explicit private peer resolution, account-scoped conversation keys, typed identity failures, tri-state authorship, relation and multi-state models.
- Added independent `/sync/sync_msg` record parsing; sync data is never represented as a synthetic 11013 callback.
- Added safe callback reprs, multi-attachment models, and automated fixture leak scanning.
- Kept 11013 and room direction release-gated until the required complete real callback matrix is approved; this build is RC-only.

## 0.3.4

- Added storage URL env support for S3-compatible object stores, including custom env prefixes for host integrations.
- Added `expires_at` to resolved callback attachment targets so callers can refresh signed URLs from cached object keys.

## 0.3.3

- Presign private object-store URLs returned by Juhe private CDN download conversion when storage is configured.

## 0.3.2

- Added quoted-message callback fields for `quote_appinfo` and `quote_content`, plus `is_quote_message()`.

## 0.3.0

- Added public `QwSaasClient.request()` and `request_private()` entrypoints.
- Added default S3-compatible storage support through `StorageConfig` and `S3ObjectStorage`.
- Added private CDN wrappers for C2C/BIG/WX download and private cloud file access.
- Added callback attachment target resolution with optional storage presign.
- Added media message wrappers and URL/local-path file flow helpers.
- Added official enum classes and callback state fields for `seq`, `appinfo`, `referid`, `flag`, `content_type`, and `asid`.
- Added common account, instance, contact, room, and label wrappers.
- Added documentation for storage, local file sending, callback attachment resolution, conversation IDs, and non-owner room-list handling.

## 0.2.1

- Bumped package metadata for the `v0.2.1` patch release.
- Backfilled the missing `0.2.0` release notes.
- Refreshed README public API documentation to match the current SDK exports.

## 0.2.0

- Expanded Juhe message helpers with room mentions, message confirmation, revoke, unread reporting, and quoted message sending.
- Added contact, room, label, sync, CDN, and inbound attachment download helpers.
- Added richer callback parsing for text, image, voice, video, and file metadata.
- Added tests for the expanded HTTP helpers, callback parsing, room/contact sync, labels, sync, and inbound downloads.

## 0.1.0

- Split `qwsaas` into an independent private SDK project.
- Kept the existing HTTP API helper names for compatibility.
- Added normalized callback parsing and WebSocket protocol primitives.
- Added unit tests for HTTP calls, message helpers, file flows, WebSocket behavior, and callback parsing.

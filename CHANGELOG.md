# Changelog

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

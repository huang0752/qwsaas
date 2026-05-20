# Changelog

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

# QWSAAS

Private Python SDK for Juhe / QW SaaS enterprise WeChat integrations.

This repository owns the reusable Juhe/QW SaaS protocol layer:

- public `GuidRequest` calls through `QwSaasClient.request()`
- private CDN conversion calls through `request_private()`
- text, file, media, quote, revoke, unread, and room-at message helpers
- common account, instance, contact, room, label, sync, CDN, upload, and callback helpers
- S3-compatible object storage staging for local file sending
- WebSocket auth, receive, ack, and reconnect primitives

It does not own application-specific behavior such as Hermes gateway sessions, allowlists, mention gates, dedup policy, or tool semantics.

## Install

Local development:

```bash
uv sync --extra dev
```

Editable install from another local project:

```bash
uv pip install -e /Users/chou/code/qwsaas
```

Private Git usage should pin a tag:

```toml
juhe = [
  "qwsaas @ git+ssh://git@github.com/<private-user-or-org>/qwsaas.git@v0.4.0rc1",
]
```

`v0.4.0rc1` is intentionally incompatible with `v0.3.x`. Keep existing consumers pinned until they have migrated to the new callback models. A final `v0.4.0` tag is prohibited until the documented real callback matrix passes.

## Environment

Basic Juhe config:

```bash
export QWSAAS_APP_KEY="your-app-key"
export QWSAAS_APP_SECRET="your-app-secret"
export QWSAAS_GUID="your-guid"
export QWSAAS_PUBLIC_BASE_URL="https://chat-api.juhebot.com"
export QWSAAS_PRIVATE_BASE_URL="http://127.0.0.1:34789"
export QWSAAS_CONVERSATION_ID="S:1001"
```

`QWSAAS_PUBLIC_BASE_URL` is optional and defaults to `https://chat-api.juhebot.com`.
`QWSAAS_PRIVATE_BASE_URL` is the private CDN conversion service base, for example the service that exposes `/cloud/c2c_upload`, `/cloud/c2c_download`, `/cloud/big_upload`, `/cloud/big_download`, and `/cloud/wx_download`. It is not the S3/MinIO endpoint.

S3-compatible storage config for local file sending:

```bash
export QWSAAS_STORAGE_ENDPOINT_URL="http://127.0.0.1:9000"
export QWSAAS_STORAGE_BUCKET="wework"
export QWSAAS_STORAGE_ACCESS_KEY="..."
export QWSAAS_STORAGE_SECRET_KEY="..."
export QWSAAS_STORAGE_REGION="us-east-1"
export QWSAAS_STORAGE_PREFIX="qwsaas-temp"
export QWSAAS_STORAGE_ADDRESSING_STYLE="path"
export QWSAAS_STORAGE_URL_EXPIRES_SECONDS="3600"
```

For host-specific inbound storage, callers can keep their own prefix instead of remapping env vars:

```python
from qwsaas import S3ObjectStorage

storage = S3ObjectStorage.from_env(
    prefix="JUHE_INBOUND_S3_",
    url_env="JUHE_INBOUND_STORAGE_URL",
)
```

The URL form is similar to database and Redis URLs:

```bash
export JUHE_INBOUND_STORAGE_URL="s3+http://127.0.0.1:9000/wework?region=us-east-1&addressing_style=path&expires=3600"
export JUHE_INBOUND_S3_ACCESS_KEY="..."
export JUHE_INBOUND_S3_SECRET_KEY="..."
```

Pure `QwSaasClient(app_key, app_secret, guid)` usage does not require storage. Only helpers that send local paths or explicitly restage signed URLs need it.

## Quick Start

```python
import asyncio
import os

from qwsaas import QwSaasClient, send_text


async def main() -> None:
    client = QwSaasClient(
        app_key=os.environ["QWSAAS_APP_KEY"],
        app_secret=os.environ["QWSAAS_APP_SECRET"],
        guid=os.environ["QWSAAS_GUID"],
        public_base_url=os.environ.get("QWSAAS_PUBLIC_BASE_URL"),
        private_base_url=os.environ.get("QWSAAS_PRIVATE_BASE_URL"),
    )

    response = await send_text(
        client,
        conversation_id=os.environ["QWSAAS_CONVERSATION_ID"],
        content="hello from qwsaas",
    )
    print(response)


if __name__ == "__main__":
    asyncio.run(main())
```

Conversation IDs use Juhe's prefixes:

- direct chat: `S:<user_id>`
- room chat: `R:<room_id>`

The SDK does not reject IDs by user/room prefix shape beyond helper-level required-field checks.

## Generic Calls

Use `request()` for any public official path that does not have a typed wrapper yet:

```python
await client.request("/msg/send_text", {"conversation_id": "S:1001", "content": "hello"})
```

Use `request_private()` for configured private CDN conversion paths:

```python
await client.request_private("/cloud/wx_download", {"url": "https://imunion.weixin.qq.com/..."})
```

`request()` injects `guid` into `data`. `request_private()` does not inject business fields.

## Files And Media

URL helpers expect externally reachable URLs:

```python
from qwsaas import send_image_from_url, send_video_from_url, send_voice_from_url

await send_image_from_url(client, "S:1001", "https://files.example/a.jpg")
await send_video_from_url(client, "S:1001", "https://files.example/a.mp4")
await send_voice_from_url(client, "S:1001", "https://files.example/a.amr")
```

Local path helpers stage bytes into `S3ObjectStorage`, generate a presigned URL, send through the CDN flow, then delete the staged object by default. Image helpers upload with `file_type=2` and send through the native `/msg/send_image` endpoint; other file helpers use `/msg/send_file`.

```python
from qwsaas import S3ObjectStorage, send_file_from_path

client = QwSaasClient(..., storage=S3ObjectStorage.from_env())
await send_file_from_path(client, "S:1001", "/tmp/report.pdf")
```

The SDK never sends local filesystem paths to Juhe or the private CDN service.

For complex official media payloads, use the typed raw-payload wrappers:

```python
from qwsaas import send_image, send_media_payload

await send_image(client, {"conversation_id": "S:1001", "file_id": "...", "aes_key": "..."})
await send_media_payload(client, "/msg/send_weapp", {"conversation_id": "S:1001", "weapp": {...}})
```

## Callback And Attachments

The `0.4.0` callback API is a breaking contract. Protocol parsing is pure; account-dependent identity is a separate step:

```python
from qwsaas import (
    MessageRelation,
    logical_message_key,
    normalize_callback_identity,
    parse_callback_envelope,
)

envelope = parse_callback_envelope(payload)
normalized = normalize_callback_identity(envelope, current_account_id=current_account_id)

for message, identity in zip(envelope.messages, normalized.messages, strict=True):
    if message.message_relation is not MessageRelation.ORIGINAL:
        continue
    print(identity.provider_conversation_id, identity.account_conversation_key)
    durable_key = logical_message_key(message, current_account_id=current_account_id)
```

For private messages, `sender`, `receiver`, and `current_account_id` are compared together to determine the peer. Both directions therefore produce `S:<peer>`. Rooms produce `R:<roomid>`, but room direction remains `unknown` with `ROOM_DIRECTION_UNVERIFIED` until the real callback matrix establishes its semantics. `send_flag` is preserved as protocol data and is not treated as an echo flag.

Protocol identifiers remain separate: `appinfo` is global; `id` and `seq` are account-scoped. `logical_message_key()` uses that priority and never falls back to callback fingerprints. `envelope_event_key` and `callback_message_key` are replay fingerprints only.

Use `parse_sync_messages(records, sync_page_key=...)` for explicitly extracted `/sync/sync_msg` records. Sync results are never wrapped as synthetic 11013 callbacks. The RC rejects 11013 until a complete real batch callback is sanitized and approved.

Attachments are exposed as `message.attachments`. Sensitive fields and raw payloads are excluded from default repr; use `to_safe_dict()` for logging. Each `JuheAttachment` retains the parameters needed by the download helpers.

`resolve_callback_attachment_target()` decides whether an attachment is a public qpic URL, C2C file, private WeChat file, or big file. C2C, WeChat private media, and big-file references are resolved through the configured wework CDN `/cloud/*_download` service, and the returned URL is treated as the download target.

`download_callback_attachment()` downloads bytes from the resolved target URL, following the same plain-HTTP pattern used by the MCP delivery tools.

## Room List Note

`get_room_list()` may not return every room when the current account is not the owner. For non-owner rooms, collect `roomid` from message callbacks, then call `batch_get_room_detail()` and store the result in your application.

## Public API Groups

- Client: `QwSaasClient`, `request`, `request_private`
- Messages: `send_text`, `send_room_at`, `send_file`, `send_image`, `send_video`, `send_voice`, `send_link`, `send_weapp`, `send_quote_msg`, `revoke_msg`
- File flows: `send_file_from_url`, `send_file_from_path`, `send_image_from_url`, `send_image_from_path`, `send_video_from_url`, `send_video_from_path`, `send_voice_from_url`, `send_voice_from_path`
- Account/instance: `get_profile`, `get_corp_info`, `get_bind_wxinfo`, `set_notify_url`, `set_proxy`, `stop_client`, `restore_client`
- Contacts/rooms/tags: `sync_contact`, `sync_apply_contact`, `batch_get_userinfo`, `get_room_list`, `batch_get_room_detail`, `sync_room_info`, `sync_label_list`, `create_label`
- CDN/uploads: `get_cdn_info`, `get_cdn_file`, `c2c_upload`, `c2c_download`, `big_upload`, `big_download`, `wx_download`
- Callback/enums: `parse_callback_envelope`, `normalize_callback_identity`, `parse_sync_messages`, `logical_message_key`, `NotifyType`, `MsgType`, `MessageFlagField`, `ContactType`, `BigCdnType`

## Tests

```bash
uv run --extra dev pytest
uv run python scripts/check_callback_fixtures.py
```

The default test suite uses fake HTTP, WebSocket, and S3 clients. It does not call live Juhe endpoints, the private CDN service, or real S3.

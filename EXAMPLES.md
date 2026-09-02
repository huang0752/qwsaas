# QWSAAS Examples

All examples use placeholders or environment variables. Do not commit real app keys, app secrets, GUIDs, signed URLs, storage keys, or customer conversation IDs.

## Client

```python
import os

from qwsaas import QwSaasClient, S3ObjectStorage

client = QwSaasClient(
    app_key=os.environ["QWSAAS_APP_KEY"],
    app_secret=os.environ["QWSAAS_APP_SECRET"],
    guid=os.environ["QWSAAS_GUID"],
    public_base_url=os.environ.get("QWSAAS_PUBLIC_BASE_URL"),
    private_base_url=os.environ.get("QWSAAS_PRIVATE_BASE_URL"),
    storage=S3ObjectStorage.from_env(),
)
```

## Send Text

```python
await send_text(client, "S:<contact-id>", "hello")
```

## Generic Official Path

```python
await client.request(
    "/msg/send_text",
    {"conversation_id": "S:<contact-id>", "content": "hello"},
)
```

## Send Local File

```python
from qwsaas import send_file_from_path

await send_file_from_path(
    client,
    conversation_id="S:<contact-id>",
    file_path="/tmp/report.pdf",
)
```

The helper uploads `/tmp/report.pdf` to configured S3-compatible storage, presigns a GET URL, sends through the private CDN flow, and deletes the temporary object.

## Send Image, Video, Voice From URL

```python
from qwsaas import send_image_from_url, send_video_from_url, send_voice_from_url

await send_image_from_url(client, "S:<contact-id>", "https://files.example/a.jpg")
await send_video_from_url(client, "R:<room-id>", "https://files.example/a.mp4")
await send_voice_from_url(client, "S:<contact-id>", "https://files.example/a.amr")
```

## Resolve Callback Attachment

```python
from qwsaas import resolve_callback_attachment_target

attachment = message.attachments[0]
target = await resolve_callback_attachment_target(
    client,
    download_url=attachment.download_url or "",
    file_id=attachment.file_id,
    file_name=attachment.file_name,
    file_size=attachment.file_size,
    aes_key=attachment.aes_key,
    auth_key=attachment.auth_key,
    auth_cookies=attachment.auth_cookies,
    attachment_kind=attachment.kind.value,
    mime_type=attachment.mime_type,
    is_hd=attachment.is_hd,
    base_request=attachment.base_request,
)

print(target.url)
```

## Download Callback Attachment Bytes

```python
from qwsaas import download_callback_attachment

media = message.attachments[0]
attachment = await download_callback_attachment(
    client,
    download_url=media.download_url or "",
    file_id=media.file_id,
    file_name=media.file_name,
    file_size=media.file_size,
    aes_key=media.aes_key,
    auth_key=media.auth_key,
    auth_cookies=media.auth_cookies,
    attachment_kind=media.kind.value,
    mime_type=media.mime_type,
    is_hd=media.is_hd,
    base_request=media.base_request,
    max_bytes=20 * 1024 * 1024,
)
```

## Tags

```python
from qwsaas import contact_add_label, create_label, delete_label

created = await create_label(client, {"label_name": "qwsaas-test"})
await contact_add_label(client, {"user_id": "788...", "label_id": "label-id"})
await delete_label(client, {"label_id": "label-id"})
```

## Rooms

```python
from qwsaas import invite_room_member, remove_room_member

await invite_room_member(client, {"room_id": "10...", "user_list": ["788..."]})
await remove_room_member(client, {"room_id": "10...", "user_list": ["788..."]})
```

## Callback State

```python
from qwsaas import (
    MessageRelation,
    MessageStateKind,
    logical_message_key,
    normalize_callback_identity,
    parse_callback_envelope,
)

envelope = parse_callback_envelope(payload)
identity = normalize_callback_identity(envelope, current_account_id="ACCOUNT_A")

for message, normalized in zip(envelope.messages, identity.messages, strict=True):
    if message.message_relation is MessageRelation.ORIGINAL:
        key = logical_message_key(message, current_account_id="ACCOUNT_A")
        print(normalized.provider_conversation_id, key.to_safe_dict())
    if MessageStateKind.REVOKE in message.state_kinds:
        print("message was revoked")
```

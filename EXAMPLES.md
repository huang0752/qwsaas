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

target = await resolve_callback_attachment_target(
    client,
    download_url=message.download_url or "",
    file_id=message.file_id,
    file_name=message.file_name,
    file_size=message.file_size,
    aes_key=message.aes_key,
    auth_key=message.auth_key,
    attachment_kind=message.attachment_kind,
    mime_type=message.mime_type,
    is_hd=message.is_hd,
    base_request=message.base_request,
)

print(target.url)
```

## Download Callback Attachment Bytes

```python
from qwsaas import download_callback_attachment

attachment = await download_callback_attachment(
    client,
    download_url=message.download_url or "",
    file_id=message.file_id,
    file_name=message.file_name,
    file_size=message.file_size,
    aes_key=message.aes_key,
    auth_key=message.auth_key,
    attachment_kind=message.attachment_kind,
    mime_type=message.mime_type,
    is_hd=message.is_hd,
    base_request=message.base_request,
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
from qwsaas import MessageFlagField, has_message_flag, is_original_message, parse_callback_envelope

envelope = parse_callback_envelope(payload)
if envelope:
    for message in envelope.messages:
        if not is_original_message(message):
            continue
        if has_message_flag(message, MessageFlagField.MessageFlagFieldRevoke):
            print("message was revoked", message.appinfo)
```

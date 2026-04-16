# QWSAAS Examples

All examples use placeholders or environment variables. Do not commit real app keys, app secrets, GUIDs, upload URLs, or customer conversation IDs.

## Public GuidRequest Shape

```json
{
  "app_key": "<QWSAAS_APP_KEY>",
  "app_secret": "<QWSAAS_APP_SECRET>",
  "path": "/msg/send_text",
  "data": {
    "guid": "<QWSAAS_GUID>",
    "conversation_id": "S:<contact-id-or-vid>",
    "content": "hello"
  }
}
```

## Send Text

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
    )
    await send_text(client, os.environ["QWSAAS_CONVERSATION_ID"], "hello")


asyncio.run(main())
```

## Send Big File From URL

```python
import asyncio
import os

from qwsaas import QwSaasClient, send_big_file_from_url


async def main() -> None:
    client = QwSaasClient(
        app_key=os.environ["QWSAAS_APP_KEY"],
        app_secret=os.environ["QWSAAS_APP_SECRET"],
        guid=os.environ["QWSAAS_GUID"],
        public_base_url=os.environ.get("QWSAAS_PUBLIC_BASE_URL"),
        private_base_url=os.environ["QWSAAS_PRIVATE_BASE_URL"],
        timeout_seconds=600,
    )
    await send_big_file_from_url(
        client,
        conversation_id=os.environ["QWSAAS_CONVERSATION_ID"],
        file_url=os.environ["QWSAAS_FILE_URL"],
        file_name=os.environ.get("QWSAAS_FILE_NAME", "example.zip"),
        file_type=int(os.environ.get("QWSAAS_FILE_TYPE", "5")),
    )


asyncio.run(main())
```

## Parse Callback

```python
from qwsaas import parse_callback_envelope

parsed = parse_callback_envelope({
    "type": "callback",
    "event_id": "evt-1",
    "event": {
        "guid": "<QWSAAS_GUID>",
        "notify_type": 11010,
        "data": {
            "msg_type": 2,
            "content": "{\"msg\":\"hello\"}",
            "sender": "1001",
            "msg_id": "msg-1"
        }
    }
})

if parsed:
    for message in parsed.messages:
        print(message.conversation_id, message.text)
```

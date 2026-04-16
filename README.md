# QWSAAS

Private Python SDK for Juhe / QW SaaS enterprise WeChat integrations.

This repository is intentionally kept independent from product applications. It owns the reusable protocol layer for Juhe/QW SaaS:

- `GuidRequest` public API calls
- private upload endpoint calls
- text and file message helpers
- small-file and big-file upload/send flows
- WebSocket auth, receive, ack, and reconnect primitives
- callback envelope parsing into SDK-level message objects
- shared exceptions and response normalization

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

Future Hermes usage should pin a private Git tag or commit, for example:

```toml
juhe = [
  "qwsaas @ git+ssh://git@github.com/<private-user-or-org>/qwsaas.git@v0.1.0",
]
```

## Environment

Examples expect credentials and runtime settings from environment variables:

```bash
export QWSAAS_APP_KEY="your-app-key"
export QWSAAS_APP_SECRET="your-app-secret"
export QWSAAS_GUID="your-guid"
export QWSAAS_PUBLIC_BASE_URL="https://chat-api.juhebot.com"
export QWSAAS_PRIVATE_BASE_URL="https://private-upload.example"
export QWSAAS_CONVERSATION_ID="S:1001"
```

`QWSAAS_PUBLIC_BASE_URL` is optional and defaults to `https://chat-api.juhebot.com`.
`QWSAAS_PRIVATE_BASE_URL` is required only for private upload flows.

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

## Public API

- `QwSaasClient`
- `send_text(client, conversation_id, content)`
- `send_file(client, conversation_id, file_id, file_name, size, md5, aes_key=None)`
- `get_room_list(client, start_index=0, limit=10)`
- `get_cdn_info(client)`
- `get_wwfile_auth_key(client, file_key, file_type)`
- `c2c_to_wwfile_id(client, file_id, file_md5, file_size, file_key)`
- `c2c_upload(client, base_request, file_type, url)`
- `big_upload(client, appid, auth_key, base_request, file_key, url, guid=None)`
- `send_small_file_from_url(client, conversation_id, file_url, file_name, file_type=5)`
- `send_big_file_from_url(client, conversation_id, file_url, file_name, file_type=5)`
- `JuheWsClient`
- `parse_callback_envelope(payload)`

## Tests

```bash
uv run --extra dev pytest
```

The test suite uses fake HTTP and WebSocket transports. It does not call live Juhe endpoints.

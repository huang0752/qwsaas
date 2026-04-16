from __future__ import annotations

import asyncio
import os

from qwsaas import QwSaasClient, send_small_file_from_url, send_text


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
        content=os.environ.get("QWSAAS_TEXT", "hello from qwsaas"),
    )
    print(response)

    file_url = os.environ.get("QWSAAS_FILE_URL")
    if file_url:
        file_response = await send_small_file_from_url(
            client,
            conversation_id=os.environ["QWSAAS_CONVERSATION_ID"],
            file_url=file_url,
            file_name=os.environ.get("QWSAAS_FILE_NAME", "example.txt"),
        )
        print(file_response)


if __name__ == "__main__":
    asyncio.run(main())

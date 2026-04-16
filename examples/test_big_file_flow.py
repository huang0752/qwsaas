from __future__ import annotations

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
        timeout_seconds=float(os.environ.get("QWSAAS_TIMEOUT_SECONDS", "600")),
    )

    response = await send_big_file_from_url(
        client,
        conversation_id=os.environ["QWSAAS_CONVERSATION_ID"],
        file_url=os.environ["QWSAAS_FILE_URL"],
        file_name=os.environ.get("QWSAAS_FILE_NAME", "example.zip"),
        file_type=int(os.environ.get("QWSAAS_FILE_TYPE", "5")),
    )
    print(response)


if __name__ == "__main__":
    asyncio.run(main())

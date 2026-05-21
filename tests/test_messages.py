from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from qwsaas.exceptions import QwSaasRequestError
from qwsaas.messages import (
    apply_voice_id,
    confirm_msg,
    query_voice_text,
    report_unread,
    revoke_msg,
    send_file,
    send_gif,
    send_gif_url,
    send_image,
    send_link,
    send_location,
    send_media_payload,
    send_personal_card,
    send_quote_msg,
    send_room_at,
    send_text,
    send_video,
    send_big_video,
    send_voice,
    send_weapp,
)


@pytest.mark.asyncio
async def test_send_text_validates_required_arguments() -> None:
    client = SimpleNamespace(_request_public=AsyncMock())

    with pytest.raises(QwSaasRequestError, match="conversation_id"):
        await send_text(client, "", "hello")

    with pytest.raises(QwSaasRequestError, match="content"):
        await send_text(client, "S:1001", "")


@pytest.mark.asyncio
async def test_send_text_posts_expected_payload() -> None:
    client = SimpleNamespace(_request_public=AsyncMock(return_value={"error_code": 0}))

    result = await send_text(client, "S:1001", "hello")

    assert result == {"error_code": 0}
    client._request_public.assert_awaited_once_with(
        "/msg/send_text",
        data={"conversation_id": "S:1001", "content": "hello"},
    )


@pytest.mark.asyncio
async def test_send_media_payload_preserves_unknown_fields() -> None:
    client = SimpleNamespace(_request_public=AsyncMock(return_value={"ok": True}))

    await send_media_payload(client, "/msg/send_image", {"conversation_id": "S:1001", "extra": "keep"})

    client._request_public.assert_awaited_once_with(
        "/msg/send_image",
        data={"conversation_id": "S:1001", "extra": "keep"},
    )


@pytest.mark.asyncio
async def test_send_media_payload_validates_path_and_payload() -> None:
    client = SimpleNamespace(_request_public=AsyncMock())

    with pytest.raises(QwSaasRequestError, match="path"):
        await send_media_payload(client, "", {"conversation_id": "S:1001"})

    with pytest.raises(QwSaasRequestError, match="payload"):
        await send_media_payload(client, "/msg/send_image", ["bad"])  # type: ignore[arg-type]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("wrapper", "path"),
    [
        (send_voice, "/msg/send_voice"),
        (send_location, "/msg/send_location"),
        (send_image, "/msg/send_image"),
        (send_video, "/msg/send_video"),
        (send_big_video, "/msg/send_big_video"),
        (send_gif, "/msg/send_gif"),
        (send_gif_url, "/msg/send_gif_url"),
        (send_personal_card, "/msg/send_personal_card"),
        (send_link, "/msg/send_link"),
        (send_weapp, "/msg/send_weapp"),
        (apply_voice_id, "/msg/apply_voice_id"),
        (query_voice_text, "/msg/query_voice_text"),
    ],
)
async def test_media_wrappers_post_expected_paths(wrapper: object, path: str) -> None:
    client = SimpleNamespace(_request_public=AsyncMock(return_value={"ok": True}))

    await wrapper(client, {"conversation_id": "S:1001", "official": {"field": "keep"}})

    client._request_public.assert_awaited_once_with(
        path,
        data={"conversation_id": "S:1001", "official": {"field": "keep"}},
    )


@pytest.mark.asyncio
async def test_send_file_validates_required_arguments() -> None:
    client = SimpleNamespace(_request_public=AsyncMock())

    with pytest.raises(QwSaasRequestError, match="file_id"):
        await send_file(client, "S:1001", "", "a.txt", 1, "md5")

    with pytest.raises(QwSaasRequestError, match="file_name"):
        await send_file(client, "S:1001", "file-id", "", 1, "md5")

    with pytest.raises(QwSaasRequestError, match="size"):
        await send_file(client, "S:1001", "file-id", "a.txt", 0, "md5")

    with pytest.raises(QwSaasRequestError, match="md5"):
        await send_file(client, "S:1001", "file-id", "a.txt", 1, "")


@pytest.mark.asyncio
async def test_send_file_includes_optional_aes_key() -> None:
    client = SimpleNamespace(_request_public=AsyncMock(return_value={"error_code": 0}))

    await send_file(client, "S:1001", "file-id", "a.txt", 10, "md5", aes_key="aes")

    client._request_public.assert_awaited_once_with(
        "/msg/send_file",
        data={
            "conversation_id": "S:1001",
            "file_id": "file-id",
            "file_name": "a.txt",
            "size": 10,
            "md5": "md5",
            "aes_key": "aes",
        },
    )


@pytest.mark.asyncio
async def test_send_room_at_validates_required_arguments() -> None:
    client = SimpleNamespace(_request_public=AsyncMock())

    with pytest.raises(QwSaasRequestError, match="conversation_id"):
        await send_room_at(client, "", "hello {$@}", ["1001"])

    with pytest.raises(QwSaasRequestError, match="content"):
        await send_room_at(client, "R:2001", "", ["1001"])

    with pytest.raises(QwSaasRequestError, match="at_list"):
        await send_room_at(client, "R:2001", "hello {$@}", [])


@pytest.mark.asyncio
async def test_send_room_at_posts_expected_payload() -> None:
    client = SimpleNamespace(_request_public=AsyncMock(return_value={"error_code": 0}))

    await send_room_at(client, "R:2001", "hello {$@}", ["1001", 0])

    client._request_public.assert_awaited_once_with(
        "/msg/send_room_at",
        data={
            "conversation_id": "R:2001",
            "content": "hello {$@}",
            "at_list": ["1001", 0],
        },
    )


@pytest.mark.asyncio
async def test_confirm_msg_validates_required_arguments() -> None:
    client = SimpleNamespace(_request_public=AsyncMock())

    with pytest.raises(QwSaasRequestError, match="message_type"):
        await confirm_msg(client, -1, sender="1001", receiver="1002", msgid="msg-1")

    with pytest.raises(QwSaasRequestError, match="sender"):
        await confirm_msg(client, 2, sender="", receiver="1002", msgid="msg-1")

    with pytest.raises(QwSaasRequestError, match="receiver"):
        await confirm_msg(client, 2, sender="1001", receiver="", msgid="msg-1")

    with pytest.raises(QwSaasRequestError, match="msgid"):
        await confirm_msg(client, 2, sender="1001", receiver="1002", msgid="")


@pytest.mark.asyncio
async def test_confirm_msg_posts_expected_payload() -> None:
    client = SimpleNamespace(_request_public=AsyncMock(return_value={"error_code": 0}))

    await confirm_msg(
        client,
        2,
        sender="1001",
        receiver="1002",
        roomid="2001",
        msgid="msg-1",
    )

    client._request_public.assert_awaited_once_with(
        "/msg/confirm_msg",
        data={
            "message_type": 2,
            "sender": "1001",
            "receiver": "1002",
            "roomid": "2001",
            "msgid": "msg-1",
        },
    )


@pytest.mark.asyncio
async def test_revoke_msg_validates_required_arguments() -> None:
    client = SimpleNamespace(_request_public=AsyncMock())

    with pytest.raises(QwSaasRequestError, match="conversation_id"):
        await revoke_msg(client, "", "msg-1")

    with pytest.raises(QwSaasRequestError, match="msgid"):
        await revoke_msg(client, "S:1001", "")


@pytest.mark.asyncio
async def test_revoke_msg_posts_expected_payload() -> None:
    client = SimpleNamespace(_request_public=AsyncMock(return_value={"error_code": 0}))

    await revoke_msg(client, "S:1001", "msg-1")

    client._request_public.assert_awaited_once_with(
        "/msg/revoke_msg",
        data={"conversation_id": "S:1001", "msgid": "msg-1"},
    )


@pytest.mark.asyncio
async def test_report_unread_validates_required_arguments() -> None:
    client = SimpleNamespace(_request_public=AsyncMock())

    with pytest.raises(QwSaasRequestError, match="conversation_id"):
        await report_unread(client, "")


@pytest.mark.asyncio
async def test_report_unread_posts_expected_payload() -> None:
    client = SimpleNamespace(_request_public=AsyncMock(return_value={"error_code": 0}))

    await report_unread(client, "R:2001")

    client._request_public.assert_awaited_once_with(
        "/msg/report_unread",
        data={"conversation_id": "R:2001"},
    )


@pytest.mark.asyncio
async def test_send_quote_msg_validates_required_arguments() -> None:
    client = SimpleNamespace(_request_public=AsyncMock())
    message = {"msg_type": 2, "content": "quoted"}

    with pytest.raises(QwSaasRequestError, match="conversation_id"):
        await send_quote_msg(
            client,
            conversation_id="",
            quote="quoted",
            content="reply",
            appinfo="appinfo-1",
            content_type=2,
            sender="1001",
            sender_name="Alice",
            message=message,
        )

    with pytest.raises(QwSaasRequestError, match="quote"):
        await send_quote_msg(
            client,
            conversation_id="R:2001",
            quote="",
            content="reply",
            appinfo="appinfo-1",
            content_type=2,
            sender="1001",
            sender_name="Alice",
            message=message,
        )

    with pytest.raises(QwSaasRequestError, match="message.msg_type"):
        await send_quote_msg(
            client,
            conversation_id="R:2001",
            quote="quoted",
            content="reply",
            appinfo="appinfo-1",
            content_type=2,
            sender="1001",
            sender_name="Alice",
            message={"content": "quoted"},
        )


@pytest.mark.asyncio
async def test_send_quote_msg_posts_expected_payload() -> None:
    client = SimpleNamespace(_request_public=AsyncMock(return_value={"error_code": 0}))

    await send_quote_msg(
        client,
        conversation_id="R:2001",
        quote="quoted",
        content="reply",
        appinfo="appinfo-1",
        content_type=2,
        sender="1001",
        sender_name="Alice",
        message={"msg_type": 2, "content": "quoted"},
    )

    client._request_public.assert_awaited_once_with(
        "/msg/send_quote_msg",
        data={
            "conversation_id": "R:2001",
            "quote": "quoted",
            "content": "reply",
            "appinfo": "appinfo-1",
            "content_type": 2,
            "sender": "1001",
            "sender_name": "Alice",
            "message": {"msg_type": 2, "content": "quoted"},
        },
    )

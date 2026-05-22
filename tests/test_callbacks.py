from __future__ import annotations

import json

from qwsaas.callbacks import (
    NOTIFY_BATCH_NEW_MESSAGE,
    NOTIFY_NEW_MESSAGE,
    has_message_flag,
    is_original_message,
    is_quote_message,
    notify_type_name,
    parse_callback_envelope,
)
from qwsaas.enums import MessageFlagField, NotifyType


def test_parse_single_stringified_callback_message() -> None:
    parsed = parse_callback_envelope(
        {
            "type": "callback",
            "event_id": "evt-1",
            "event": json.dumps(
                {
                    "guid": "guid-1",
                    "notify_type": NOTIFY_NEW_MESSAGE,
                    "data": {
                        "msg_type": 2,
                        "content": '{"msg":"hello"}',
                        "sender": "1001",
                        "sender_name": "Alice",
                        "msg_id": "msg-1",
                    },
                }
            ),
        }
    )

    assert parsed is not None
    assert parsed.event_id == "evt-1"
    assert parsed.guid == "guid-1"
    assert parsed.notify_type == NOTIFY_NEW_MESSAGE
    assert len(parsed.messages) == 1
    message = parsed.messages[0]
    assert message.message_id == "msg-1"
    assert message.message_type == 2
    assert message.text == "hello"
    assert message.sender_id == "1001"
    assert message.sender_name == "Alice"
    assert message.conversation_id == "S:1001"
    assert message.is_group is False


def test_parse_batch_group_callback_messages() -> None:
    parsed = parse_callback_envelope(
        {
            "type": "callback",
            "event_id": "evt-2",
            "data": {
                "guid": "guid-1",
                "notify_type": NOTIFY_BATCH_NEW_MESSAGE,
                "data": [
                    {
                        "msg_type": 2,
                        "content": "hello",
                        "sender": "1001",
                        "roomid": "2001",
                        "at_list": "bot,ops",
                        "msg_id": "msg-1",
                    },
                    {
                        "msg_type": 5,
                        "content": '{"data":{"image":{"url":"https://example.test/a.jpg"}}}',
                        "sender": "1002",
                        "roomid": "2001",
                        "msg_id": "msg-2",
                    },
                ],
            },
        }
    )

    assert parsed is not None
    assert len(parsed.messages) == 2
    assert parsed.messages[0].conversation_id == "R:2001"
    assert parsed.messages[0].at_list == ("bot", "ops")
    assert parsed.messages[1].message_type == 5
    assert parsed.messages[1].text == ""
    assert parsed.messages[1].attachment_kind == "image"
    assert parsed.messages[1].download_url == "https://example.test/a.jpg"


def test_parse_file_callback_message_extracts_attachment_metadata() -> None:
    parsed = parse_callback_envelope(
        {
            "type": "callback",
            "event": {
                "guid": "guid-1",
                "notify_type": NOTIFY_NEW_MESSAGE,
                "data": {
                    "msg_type": 8,
                    "content": json.dumps(
                        {
                            "data": {
                                "file": {
                                    "file_name": "report.pdf",
                                    "file_id": "file-id",
                                    "file_key": "file-key",
                                    "file_size": 1234,
                                    "file_md5": "md5",
                                    "aes_key": "aes",
                                    "auth_key": "auth",
                                    "auth_cookies": "weixinnum=1&authkey=token",
                                    "url": "https://cdn.example/report",
                                }
                            }
                        }
                    ),
                    "sender": "1001",
                    "msg_id": "msg-file-1",
                },
            },
        }
    )

    assert parsed is not None
    message = parsed.messages[0]
    assert message.text == ""
    assert message.attachment_kind == "document"
    assert message.file_name == "report.pdf"
    assert message.file_id == "file-id"
    assert message.file_key == "file-key"
    assert message.file_size == 1234
    assert message.file_md5 == "md5"
    assert message.aes_key == "aes"
    assert message.auth_key == "auth"
    assert message.auth_cookies == "weixinnum=1&authkey=token"
    assert message.download_url == "https://cdn.example/report"
    assert message.mime_type == "application/pdf"


def test_parse_voice_and_video_callbacks_extract_attachment_kind() -> None:
    parsed = parse_callback_envelope(
        {
            "type": "callback",
            "event": {
                "guid": "guid-1",
                "notify_type": NOTIFY_BATCH_NEW_MESSAGE,
                "data": [
                    {
                        "msg_type": 6,
                        "content": {"voice": {"file_name": "voice.amr", "url": "https://cdn.example/voice"}},
                        "sender": "1001",
                        "msg_id": "voice-1",
                    },
                    {
                        "msg_type": 7,
                        "content": {"video": {"file_name": "clip.mp4", "url": "https://cdn.example/video"}},
                        "sender": "1001",
                        "msg_id": "video-1",
                    },
                ],
            },
        }
    )

    assert parsed is not None
    assert parsed.messages[0].attachment_kind == "audio"
    assert parsed.messages[0].file_name == "voice.amr"
    assert parsed.messages[0].mime_type == "audio/amr"
    assert parsed.messages[1].attachment_kind == "video"
    assert parsed.messages[1].file_name == "clip.mp4"
    assert parsed.messages[1].mime_type == "video/mp4"


def test_parse_image_callback_extracts_cdn_file_id_as_download_url() -> None:
    parsed = parse_callback_envelope(
        {
            "type": "callback",
            "event": {
                "guid": "guid-1",
                "notify_type": NOTIFY_NEW_MESSAGE,
                "data": {
                    "msg_type": 5,
                    "content_type": 101,
                    "sender": "1001",
                    "id": "img-1",
                    "file_name": "",
                    "cdn": {
                        "size": 224064,
                        "md5": "7beaa9362d4d75a5553303f727efe9b0",
                        "aes_key": "aes",
                        "is_hd": False,
                        "auth_key": "auth",
                        "file_id": "https://imunion.weixin.qq.com/cgi-bin/mmae-bin/tpdownloadmedia?param=abc",
                        "ld_file_id": "https://imunion.weixin.qq.com/cgi-bin/mmae-bin/tpdownloadmedia?param=ld",
                        "image_width": 225,
                        "image_height": 503,
                    },
                },
            },
        }
    )

    assert parsed is not None
    message = parsed.messages[0]
    assert message.attachment_kind == "image"
    assert message.download_url == "https://imunion.weixin.qq.com/cgi-bin/mmae-bin/tpdownloadmedia?param=abc"
    assert message.file_name == "image.jpg"
    assert message.file_size == 224064
    assert message.file_md5 == "7beaa9362d4d75a5553303f727efe9b0"
    assert message.aes_key == "aes"
    assert message.auth_key == "auth"
    assert message.mime_type == "image/jpeg"
    assert message.is_hd is False


def test_parse_callback_envelope_returns_none_for_empty_or_malformed_payload() -> None:
    assert parse_callback_envelope({}) is None
    assert parse_callback_envelope({"type": "callback", "event": ""}) is None
    assert parse_callback_envelope({"type": "callback", "event": "not-json"}) is None


def test_parse_callback_marks_self_echo() -> None:
    parsed = parse_callback_envelope(
        {
            "type": "callback",
            "event": {
                "guid": "guid-1",
                "notify_type": NOTIFY_NEW_MESSAGE,
                "data": {
                    "msg_type": 2,
                    "content": "bot echo",
                    "sender": "1688858038755018",
                    "roomid": "2001",
                    "send_flag": 1,
                    "id": "juhe-id-1",
                },
            },
        }
    )

    assert parsed is not None
    assert parsed.messages[0].is_self_echo is True


def test_parse_callback_extracts_message_state_fields() -> None:
    parsed = parse_callback_envelope(
        {
            "type": "callback",
            "event": {
                "guid": "guid-1",
                "notify_type": NotifyType.NotifyTypeNewMsg,
                "data": {
                    "msg_type": 2,
                    "content": "hello",
                    "sender": "1001",
                    "id": "id-1",
                    "seq": "22",
                    "appinfo": "appinfo-1",
                    "referid": "0",
                    "flag": int(
                        MessageFlagField.MessageFlagFieldHasRead
                        | MessageFlagField.MessageFlagFieldQuoteMessage
                    ),
                    "content_type": 2,
                    "asid": "asid-1",
                },
            },
        }
    )

    assert parsed is not None
    message = parsed.messages[0]
    assert message.seq == "22"
    assert message.appinfo == "appinfo-1"
    assert message.referid == "0"
    assert message.flag == 516
    assert message.content_type == 2
    assert message.asid == "asid-1"
    assert is_original_message(message) is True
    assert has_message_flag(message, MessageFlagField.MessageFlagFieldQuoteMessage) is True
    assert has_message_flag(message, MessageFlagField.MessageFlagFieldRevoke) is False
    assert notify_type_name(NotifyType.NotifyTypeNewMsg) == "NotifyTypeNewMsg"


def test_parse_callback_extracts_quote_fields() -> None:
    parsed = parse_callback_envelope(
        {
            "type": "callback",
            "event": {
                "guid": "guid-1",
                "notify_type": NotifyType.NotifyTypeNewMsg,
                "data": {
                    "msg_type": 2,
                    "content": "quote-sample-0522-5",
                    "sender": "1001",
                    "roomid": "2001",
                    "id": "1027710",
                    "seq": "9220488",
                    "appinfo": "1588540994705717994",
                    "referid": "0",
                    "flag": int(MessageFlagField.MessageFlagFieldQuoteMessage),
                    "quote_content": "「Alice：quote-sample-0522-4」\n- - -\nquote-sample-0522-5",
                    "quote_appinfo": "4530056746852165557",
                },
            },
        }
    )

    assert parsed is not None
    message = parsed.messages[0]
    assert message.quote_appinfo == "4530056746852165557"
    assert message.quote_content == "「Alice：quote-sample-0522-4」\n- - -\nquote-sample-0522-5"
    assert is_quote_message(message) is True
    assert is_original_message(message) is True


def test_parse_non_message_callback_preserves_raw_event() -> None:
    parsed = parse_callback_envelope(
        {
            "event": {
                "guid": "guid-1",
                "notify_type": NotifyType.NotifyTypeUserLogout,
                "data": "offline",
            },
        }
    )

    assert parsed is not None
    assert parsed.messages == ()
    assert parsed.raw_event["data"] == "offline"

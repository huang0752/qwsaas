from __future__ import annotations

from qwsaas.callback_messages import parse_protocol_message
from qwsaas.callback_models import AttachmentKind, CallbackParseIssueCode, MessageSource


def parse(raw: dict):
    return parse_protocol_message(
        raw,
        source=MessageSource.REALTIME_11010,
        source_event_key="event-key",
        item_index=0,
    )


def test_text_has_no_attachments() -> None:
    assert parse({"msg_type": 2, "content": "hello", "referid": "0"}).attachments == ()


def test_image_has_one_safe_structured_attachment() -> None:
    message = parse(
        {
            "msg_type": 5,
            "referid": "0",
            "content": {
                "image": {
                    "file_name": "photo.jpg",
                    "file_id": "file-1",
                    "size": 12,
                    "aes_key": "secret",
                    "url": "https://example.invalid/photo",
                }
            },
        }
    )

    assert len(message.attachments) == 1
    attachment = message.attachments[0]
    assert attachment.kind is AttachmentKind.IMAGE
    assert attachment.file_id == "file-1"
    assert attachment.file_size == 12


def test_unverified_mixed_shape_is_preserved_as_issue() -> None:
    message = parse({"msg_type": 13, "referid": "0", "content": {"items": [{"type": 5}]}})
    assert message.attachments == ()
    assert CallbackParseIssueCode.UNSUPPORTED_ATTACHMENT_SHAPE in {item.code for item in message.parse_issues}


def test_documented_single_media_kinds_keep_download_fields() -> None:
    cases = [
        (5, "image", "image", "image/jpeg"),
        (6, "voice", "audio", "audio/amr"),
        (7, "video", "video", "video/mp4"),
        (8, "file", "document", "application/pdf"),
    ]
    for msg_type, payload_key, kind, mime_type in cases:
        message = parse(
            {
                "msg_type": msg_type,
                "referid": "0",
                "content": {
                    "data": {
                        payload_key: {
                            "file_name": "sample.pdf" if msg_type == 8 else None,
                            "file_id": "FILE_A",
                            "size": 12,
                            "aes_key": "SECRET_A",
                            "auth_key": "SECRET_B",
                            "auth_cookies": "SECRET_C",
                            "url": "https://example.invalid/media",
                        }
                    }
                },
            }
        )
        attachment = message.attachments[0]
        assert attachment.kind.value == kind
        assert attachment.mime_type == mime_type
        assert attachment.file_id == "FILE_A"
        assert attachment.aes_key == "SECRET_A"


def test_top_level_cdn_payload_is_supported_for_image() -> None:
    message = parse(
        {
            "msg_type": 5,
            "referid": "0",
            "cdn": {
                "file_id": "https://example.invalid/media",
                "size": 12,
                "md5": "MD5_A",
                "aes_key": "AES_A",
                "auth_key": "AUTH_A",
                "is_hd": "false",
            },
        }
    )
    attachment = message.attachments[0]
    assert attachment.download_url == "https://example.invalid/media"
    assert attachment.is_hd is False

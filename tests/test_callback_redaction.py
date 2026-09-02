from __future__ import annotations

from qwsaas import (
    logical_message_key,
    normalize_callback_identity,
    parse_callback_envelope,
)
from qwsaas.callback_models import AttachmentKind, JuheAttachment


def test_attachment_repr_and_safe_dict_hide_sensitive_values() -> None:
    attachment = JuheAttachment(
        kind=AttachmentKind.IMAGE,
        file_name="SECRET_NAME",
        file_id="SECRET_ID",
        file_key="SECRET_FILE_KEY",
        file_size=12,
        file_md5="SECRET_MD5",
        aes_key="SECRET_AES",
        auth_key="SECRET_AUTH",
        auth_cookies="SECRET_COOKIE",
        download_url="https://example.invalid/media?sig=SECRET_URL",
        mime_type="image/jpeg",
        is_hd=False,
        base_request={"token": "SECRET_BASE"},
        raw_payload={"content": "SECRET_CONTENT"},
    )

    rendered = repr(attachment) + repr(attachment.to_safe_dict())
    secrets = (
        "SECRET_NAME",
        "SECRET_ID",
        "SECRET_FILE_KEY",
        "SECRET_MD5",
        "SECRET_AES",
        "SECRET_AUTH",
        "SECRET_COOKIE",
        "SECRET_URL",
        "SECRET_BASE",
        "SECRET_CONTENT",
    )
    assert all(secret not in rendered for secret in secrets)
    assert attachment.to_safe_dict() == {
        "kind": "image",
        "file_size": 12,
        "mime_type": "image/jpeg",
        "is_hd": False,
        "has_file_id": True,
        "has_download_url": True,
    }


def test_envelope_message_identity_and_key_reprs_hide_raw_content_and_ids() -> None:
    secret_values = ("SECRET_GUID", "SECRET_ACCOUNT", "SECRET_CONTACT", "SECRET_CONTENT", "SECRET_APPINFO")
    envelope = parse_callback_envelope(
        {
            "guid": "SECRET_GUID",
            "notify_type": 11010,
            "data": {
                "id": "SECRET_LOCAL",
                "seq": "SECRET_SEQ",
                "appinfo": "SECRET_APPINFO",
                "sender": "SECRET_CONTACT",
                "receiver": "SECRET_ACCOUNT",
                "roomid": "0",
                "msg_type": 2,
                "referid": "0",
                "content": "SECRET_CONTENT",
            },
        }
    )
    normalized = normalize_callback_identity(envelope, current_account_id="SECRET_ACCOUNT")
    logical_key = logical_message_key(envelope.messages[0])
    rendered = repr(envelope) + repr(envelope.messages[0]) + repr(normalized) + repr(logical_key)
    assert all(value not in rendered for value in secret_values)

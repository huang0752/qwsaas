from __future__ import annotations

from qwsaas.enums import (
    AddFriendSourceType,
    BigCdnType,
    ContactType,
    MessageFlagField,
    MsgType,
    NotifyType,
    QrcodeStatus,
)


def test_official_notify_type_values() -> None:
    assert NotifyType.NotifyTypeNewMsg == 11010
    assert NotifyType.NotifyTypeBatchNewMsg == 11013
    assert NotifyType.NotifyTypeFriendChange == 2131


def test_official_qrcode_status_values() -> None:
    assert QrcodeStatus.QRCODE_LOGIN_NEVER == 0
    assert QrcodeStatus.QRCODE_REQUIRE_VERIFY == 10


def test_official_msg_type_values() -> None:
    assert MsgType.MsgTypeText == 2
    assert MsgType.MsgTypeImage == 5
    assert MsgType.MsgTypeFile == 8
    assert MsgType.MsgTypeReadReport == 1012


def test_message_flag_field_supports_bitwise_checks() -> None:
    flag = MessageFlagField.MessageFlagFieldHasRead | MessageFlagField.MessageFlagFieldQuoteMessage

    assert flag & MessageFlagField.MessageFlagFieldHasRead
    assert flag & MessageFlagField.MessageFlagFieldQuoteMessage
    assert not flag & MessageFlagField.MessageFlagFieldRevoke


def test_official_contact_and_cdn_values() -> None:
    assert ContactType.ContactTypeNil == 0
    assert ContactType.ContactTypeDel == 2049
    assert ContactType.ContactTypeAdd == 2057
    assert AddFriendSourceType.ADDFRIENDSOURCETYPE_SEARCH == 4
    assert AddFriendSourceType.ADDFRIENDSOURCETYPE_FROM_WHITE_LIST == 163
    assert BigCdnType.BigCdnTypeImage == 1
    assert BigCdnType.BigCdnTypeImageThumb == 3

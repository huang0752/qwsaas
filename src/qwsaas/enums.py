from __future__ import annotations

from enum import IntEnum, IntFlag


class NotifyType(IntEnum):
    NotifyTypeUnknown = 0
    NotifyTypeManagerSendTask = 573
    NotifyTypeReady = 11001
    NotifyTypeLoginQRCodeChange = 11002
    NotifyTypeUserLogin = 11003
    NotifyTypeUserLogout = 11004
    NotifyTypeInitFinish = 11005
    NotifyTypeHeartBeatError = 11006
    NotifyTypeSessionTimeout = 11007
    NotifyTypeLoginFailed = 11008
    NotifyTypeContactSyncFinish = 11009
    NotifyTypeNewMsg = 11010
    NotifyTypeLoginOtherDevice = 11011
    NotifyTypeLoginSafeVerify = 11012
    NotifyTypeBatchNewMsg = 11013
    NotifyTypeFriendChange = 2131
    NotifyTypeFriendApply = 2132
    NotifyTypeRoomNameChange = 1001
    NotifyTypeRoomDismiss = 1023
    NotifyTypeSystemTips = 1037
    NotifyTypeRoomInfoChange = 2118
    NotifyTypeRoomMemberAdd = 1002
    NotifyTypeRoomMemberDel = 1003
    NotifyTypeRoomKickMember = 1004
    NotifyTypeRoomExit = 1005
    NotifyTypeRoomCreate = 1006
    NotifyTypeRoomConfirmAddMemberNotify = 1029
    NotifyTypeMutaInfoChange = 2115
    NotifyTypeVoipNotify = 2166
    NotifyTypeWeWorkVoipNotify = 2120
    NotifyTypeSnsChangeNotify = 2215
    NotifyTypeSnsNotify = 529
    NotifyTypeAdminTipsNotify = 573


class QrcodeStatus(IntEnum):
    QRCODE_LOGIN_NEVER = 0
    QRCODE_LOGIN_ING = 1
    QRCODE_LOGIN_SUCC = 2
    QRCODE_LOGIN_FAIL = 3
    QRCODE_LOGIN_REFUSE = 4
    QRCODE_LOGIN_ING_WX = 5
    QRCODE_LOGIN_SUCC_WX = 6
    QRCODE_LOGIN_FAIL_WX = 7
    QRCODE_LOGIN_REFUSE_WX = 8
    QRCODE_WX_AUTH_OK = 9
    QRCODE_REQUIRE_VERIFY = 10


class MsgType(IntEnum):
    MsgTypeNil = 0
    MsgTypeRevoke = 1
    MsgTypeText = 2
    MsgTypeLocation = 3
    MsgTypeLink = 4
    MsgTypeImage = 5
    MsgTypeVoice = 6
    MsgTypeVideo = 7
    MsgTypeFile = 8
    MsgTypeHongBao = 9
    MsgTypeGif = 10
    MsgTypePersonalCard = 11
    MsgTypeWeApp = 12
    MsgTypeMixed = 13
    MsgTypeSphFeed = 14
    MsgTypeAppTextCard = 15
    MsgTypeMergeMsg = 16
    MsgTypeSystem = 1011
    MsgTypeReadReport = 1012


class MessageFlagField(IntFlag):
    MessageFlagFieldNil = 0
    MessageFlagFieldDel = 1
    MessageFlagFieldAck = 2
    MessageFlagFieldHasRead = 4
    MessageFlagFieldHasAtMe = 8
    MessageFlagFieldHadAck = 16
    MessageFlagFieldRevoke = 32
    MessageFlagFieldPrivateClock = 64
    MessageFlagFieldPublicClock = 128
    MessageFlagFieldDelClock = 256
    MessageFlagFieldQuoteMessage = 512
    MessageFlagFieldClockArriveInvalid = 1024
    MessageFlagFieldAnonymous = 2048
    MessageFlagFieldRevokeByAck = 4128
    MessageFlagFieldEncrypt = 8192
    MessageFlagFieldReceiptMode = 16384
    MessageFlagFieldThirdPartyEncrypt = 32768
    MessageFlagFieldRoomNotice = 65536
    MessageFlagFieldReadReceipt = 131072
    MessageFlagFieldHidden = 262144
    MessageFlagFieldWeChatFriend = 524288
    MessageFlagFieldThirdApi = 1048576
    MessageFlagFieldFromKF = 2097152
    MessageFlagFieldSendFail = 4194304
    MessageFlagFieldOurDepartmentReadMode = 8388608
    MessageFlagFieldWWWXOutRoom = 16777216
    MessageFlagFieldServerRetrySuccess = 33554432
    MessageFlagFieldKfTips = 134217728


class ContactType(IntEnum):
    ContactTypeNil = 0
    ContactTypeDelByUser = 8
    ContactTypeDel = 2049
    ContactTypeAdd = 2057


class AddFriendSourceType(IntEnum):
    ADDFRIENDSOURCETYPE_NEW = 1
    ADDFRIENDSOURCETYPE_WEIXIN = 2
    ADDFRIENDSOURCETYPE_PHONE = 3
    ADDFRIENDSOURCETYPE_SEARCH = 4
    ADDFRIENDSOURCETYPE_COLLEAGUE = 5
    ADDFRIENDSOURCETYPE_COLLEAGUE_CHAT = 6
    ADDFRIENDSOURCETYPE_VERIFIED_END = 100
    ADDFRIENDSOURCETYPE_CARD = 101
    ADDFRIENDSOURCETYPE_ROOM = 102
    ADDFRIENDSOURCETYPE_SWEEP = 103
    ADDFRIENDSOURCETYPE_SINGLEFRIEND = 104
    ADDFRIENDSOURCETYPE_BUSINESSCARD = 106
    ADDFRIENDSOURCETYPE_SEARCH_MOBILE = 118
    ADDFRIENDSOURCETYPE_SEARCH_WXID = 119
    ADDFRIENDSOURCETYPE_SEARCH_QQNUM = 120
    ADDFRIENDSOURCETYPE_SEARCH_MAIL = 123
    ADDFRIENDSOURCETYPE_WEIXIN_RECOMMEND = 124
    ADDFRIENDSOURCETYPE_ADD_WXWORK = 125
    ADDFRIENDSOURCETYPE_SCAN_CARD = 126
    ADDFRIENDSOURCETYPE_SUCCEED = 141
    ADDFRIENDSOURCETYPE_MEETING_PROFILE = 146
    ADDFRIENDSOURCETYPE_FROM_WHITE_LIST = 163


class BigCdnType(IntEnum):
    BigCdnTypeNil = 0
    BigCdnTypeImage = 1
    BigCdnTypeVideo = 2
    BigCdnTypeImageThumb = 3

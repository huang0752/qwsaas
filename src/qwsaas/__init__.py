"""Private QW SaaS SDK for Juhe enterprise WeChat integrations."""

from .callbacks import NOTIFY_BATCH_NEW_MESSAGE, NOTIFY_NEW_MESSAGE, parse_callback_envelope
from .cdn import (
    c2c_to_wwfile_id,
    get_cdn_file,
    get_cdn_info,
    get_wwfile_auth_key,
    get_wwfile_download_info,
)
from .client import QwSaasClient
from .contacts import batch_get_userinfo, search_contact, sync_contact
from .exceptions import (
    ErrorCode,
    QwSaasApiError,
    QwSaasError,
    QwSaasHttpError,
    QwSaasPrivateObjectAccessError,
    QwSaasRequestError,
    QwSaasResponseError,
    QwSaasStorageConfigError,
    QwSaasStorageError,
)
from .file_flows import send_big_file_from_url, send_small_file_from_url
from .inbound_downloads import download_callback_attachment, resolve_callback_attachment_target
from .messages import (
    confirm_msg,
    report_unread,
    revoke_msg,
    send_file,
    send_quote_msg,
    send_room_at,
    send_text,
)
from .models import (
    DownloadedAttachment,
    JuheApiResponse,
    JuheCallbackEnvelope,
    JuheCallbackMessage,
    ResolvedAttachmentTarget,
)
from .rooms import batch_get_member_detail, batch_get_room_detail, get_room_list, sync_room_info
from .storage import S3ObjectStorage, StorageConfig, StoredObject
from .sync import sync_msg, sync_multi_data
from .tags import sync_label_list
from .uploads import big_download, big_upload, c2c_download, c2c_upload, upload_video_preview, wx_download
from .ws import DEFAULT_WS_URL, JuheWsClient

__all__ = [
    "DEFAULT_WS_URL",
    "big_download",
    "big_upload",
    "batch_get_member_detail",
    "batch_get_room_detail",
    "batch_get_userinfo",
    "c2c_to_wwfile_id",
    "c2c_download",
    "c2c_upload",
    "confirm_msg",
    "download_callback_attachment",
    "DownloadedAttachment",
    "ErrorCode",
    "get_cdn_file",
    "get_cdn_info",
    "get_room_list",
    "get_wwfile_auth_key",
    "get_wwfile_download_info",
    "JuheApiResponse",
    "JuheCallbackEnvelope",
    "JuheCallbackMessage",
    "JuheWsClient",
    "NOTIFY_BATCH_NEW_MESSAGE",
    "NOTIFY_NEW_MESSAGE",
    "QwSaasApiError",
    "QwSaasClient",
    "QwSaasError",
    "QwSaasHttpError",
    "QwSaasPrivateObjectAccessError",
    "QwSaasRequestError",
    "QwSaasResponseError",
    "QwSaasStorageConfigError",
    "QwSaasStorageError",
    "ResolvedAttachmentTarget",
    "S3ObjectStorage",
    "parse_callback_envelope",
    "report_unread",
    "revoke_msg",
    "resolve_callback_attachment_target",
    "search_contact",
    "send_big_file_from_url",
    "send_small_file_from_url",
    "send_file",
    "send_quote_msg",
    "send_room_at",
    "send_text",
    "sync_contact",
    "sync_label_list",
    "sync_msg",
    "sync_multi_data",
    "sync_room_info",
    "StorageConfig",
    "StoredObject",
    "upload_video_preview",
    "wx_download",
]

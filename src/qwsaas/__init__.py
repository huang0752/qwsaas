"""Private QW SaaS SDK for Juhe enterprise WeChat integrations."""

from .callbacks import NOTIFY_BATCH_NEW_MESSAGE, NOTIFY_NEW_MESSAGE, parse_callback_envelope
from .cdn import c2c_to_wwfile_id, get_cdn_info, get_wwfile_auth_key
from .client import QwSaasClient
from .exceptions import (
    ErrorCode,
    QwSaasApiError,
    QwSaasError,
    QwSaasHttpError,
    QwSaasRequestError,
    QwSaasResponseError,
)
from .file_flows import send_big_file_from_url, send_small_file_from_url
from .messages import send_file, send_text
from .models import JuheApiResponse, JuheCallbackEnvelope, JuheCallbackMessage
from .rooms import get_room_list
from .uploads import big_upload, c2c_upload
from .ws import DEFAULT_WS_URL, JuheWsClient

__all__ = [
    "DEFAULT_WS_URL",
    "big_upload",
    "c2c_to_wwfile_id",
    "c2c_upload",
    "ErrorCode",
    "get_cdn_info",
    "get_room_list",
    "get_wwfile_auth_key",
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
    "QwSaasRequestError",
    "QwSaasResponseError",
    "parse_callback_envelope",
    "send_big_file_from_url",
    "send_small_file_from_url",
    "send_file",
    "send_text",
]

from __future__ import annotations

from enum import IntEnum, StrEnum
from typing import Any


class ErrorCode(IntEnum):
    OK = 0
    UNKNOWN = -1


class QwSaasError(Exception):
    """Base error for QW SaaS client."""


class CallbackParseErrorCode(StrEnum):
    INVALID_INPUT_TYPE = "invalid_input_type"
    MISSING_NOTIFY_TYPE = "missing_notify_type"
    INVALID_NOTIFY_TYPE = "invalid_notify_type"
    INVALID_EVENT = "invalid_event"
    CONFLICTING_EVENTS = "conflicting_events"
    INVALID_MESSAGE_PAYLOAD = "invalid_message_payload"
    UNVERIFIED_BATCH_SHAPE = "unverified_batch_shape"


class QwSaasCallbackParseError(QwSaasError):
    """Safe, structured failure produced by strict callback parsing."""

    def __init__(
        self,
        code: CallbackParseErrorCode,
        *,
        path: str,
        notify_type: int | None = None,
    ) -> None:
        self.code = code
        self.path = path
        self.notify_type = notify_type
        suffix = f" notify_type={notify_type}" if notify_type is not None else ""
        self.message = f"callback parse failed: {code.value} at {path}{suffix}"
        super().__init__(self.message)


class QwSaasRequestError(QwSaasError):
    """Invalid request arguments before sending."""


class QwSaasHttpError(QwSaasError):
    """HTTP transport or status errors."""

    def __init__(self, status_code: int, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code


class QwSaasResponseError(QwSaasError):
    """Response body parsing errors."""


class QwSaasPrivateObjectAccessError(QwSaasResponseError):
    """Resolved private object URL requires authenticated object storage access."""

    def __init__(
        self,
        message: str,
        *,
        object_url: str,
        status_code: int | None = None,
    ) -> None:
        super().__init__(message)
        self.object_url = object_url
        self.status_code = status_code


class QwSaasStorageConfigError(QwSaasError):
    """Missing or invalid object storage configuration."""


class QwSaasStorageError(QwSaasError):
    """Object storage operation failed."""


class QwSaasApiError(QwSaasError):
    """API-level error (non-zero error_code)."""

    def __init__(self, error_code: int, error_message: str, data: Any | None) -> None:
        super().__init__(f"{error_code}: {error_message}")
        self.error_code = error_code
        self.error_message = error_message
        self.data = data

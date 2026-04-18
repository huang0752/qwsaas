from __future__ import annotations

from enum import IntEnum
from typing import Any


class ErrorCode(IntEnum):
    OK = 0
    UNKNOWN = -1


class QwSaasError(Exception):
    """Base error for QW SaaS client."""


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


class QwSaasApiError(QwSaasError):
    """API-level error (non-zero error_code)."""

    def __init__(self, error_code: int, error_message: str, data: Any | None) -> None:
        super().__init__(f"{error_code}: {error_message}")
        self.error_code = error_code
        self.error_message = error_message
        self.data = data

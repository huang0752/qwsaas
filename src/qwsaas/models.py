from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class JuheApiResponse:
    """Normalized Juhe API response envelope."""

    error_code: int
    error_message: str
    data: Any
    raw: dict[str, Any]


@dataclass(frozen=True)
class DownloadedAttachment:
    """Downloaded callback attachment bytes with normalized metadata."""

    data: bytes
    file_name: str
    content_type: str


@dataclass(frozen=True)
class ResolvedAttachmentTarget:
    """Resolved callback attachment target without downloading bytes."""

    url: str
    headers: dict[str, str] | None = None
    expires_at: datetime | None = None
    object_url: str | None = None
    bucket: str | None = None
    key: str | None = None
    requires_object_store_auth: bool = False

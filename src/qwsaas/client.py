from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Any, ClassVar, Final

import httpx

from .exceptions import QwSaasApiError, QwSaasHttpError, QwSaasRequestError, QwSaasResponseError
from .models import JuheApiResponse


@dataclass(frozen=True)
class QwSaasClient:
    app_key: str
    app_secret: str
    guid: str
    private_base_url: str | None = None
    public_base_url: str | None = None
    storage: Any | None = None
    timeout_seconds: float = 30.0

    _public_url: Final[str] = "https://chat-api.juhebot.com/open/GuidRequest"

    logger: ClassVar[logging.Logger] = logging.getLogger("qwsaas.client")

    @staticmethod
    def _truncate(value: str, limit: int = 800) -> str:
        if len(value) <= limit:
            return value
        return f"{value[:limit]}..."

    async def _request_public(self, path: str, data: dict[str, Any]) -> dict[str, Any]:
        if not path:
            raise QwSaasRequestError("path is required")
        if not isinstance(data, dict):
            raise QwSaasRequestError("data must be a dict")

        payload = {
            "app_key": self.app_key,
            "app_secret": self.app_secret,
            "path": path,
            "data": {**data, "guid": self.guid},
        }
        return await self._post_json(self._resolve_public_url(), payload)

    async def request(self, path: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
        """Call any public Juhe GuidRequest path."""

        return await self._request_public(path, {} if data is None else data)

    async def _request_private(self, path: str, data: dict[str, Any]) -> dict[str, Any]:
        if not self.private_base_url:
            raise QwSaasRequestError("private_base_url is not set")
        if not path:
            raise QwSaasRequestError("path is required")
        if not isinstance(data, dict):
            raise QwSaasRequestError("data must be a dict")

        url = self.private_base_url.rstrip("/") + "/" + path.lstrip("/")
        return await self._post_json(url, data)

    async def request_private(self, path: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
        """Call a configured private CDN/storage conversion endpoint path."""

        return await self._request_private(path, {} if data is None else data)

    async def _post_json(self, url: str, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(url, json=payload)
        except httpx.HTTPError as exc:
            raise QwSaasHttpError(-1, f"HTTP error: {exc}") from exc

        if response.status_code >= 400:
            body_preview = self._truncate(response.text)
            self.logger.error(
                "QwSaas HTTP error status=%s url=%s body=%s",
                response.status_code,
                url,
                body_preview,
            )
            raise QwSaasHttpError(response.status_code, response.text)

        try:
            body = response.json()
        except ValueError as exc:
            body_preview = self._truncate(response.text)
            self.logger.error(
                "QwSaas invalid JSON response url=%s status=%s body=%s",
                url,
                response.status_code,
                body_preview,
            )
            raise QwSaasResponseError("Invalid JSON response") from exc

        if not isinstance(body, dict):
            body_preview = self._truncate(str(body))
            self.logger.error(
                "QwSaas unexpected response type url=%s body=%s",
                url,
                body_preview,
            )
            raise QwSaasResponseError("Unexpected response type")

        normalized = self._normalize_api_response(body)
        if normalized.error_code != 0:
            data_preview = self._truncate(str(normalized.data))
            self.logger.error(
                "QwSaas API error code=%s message=%s url=%s data=%s",
                normalized.error_code,
                normalized.error_message,
                url,
                data_preview,
            )
            raise QwSaasApiError(normalized.error_code, normalized.error_message, normalized.data)
        return normalized.raw

    @staticmethod
    def _normalize_api_response(body: dict[str, Any]) -> JuheApiResponse:
        base_response = body.get("baseResponse") if isinstance(body.get("baseResponse"), dict) else {}

        error_code = 0
        if "error_code" in body:
            error_code = int(body.get("error_code") or 0)
        elif isinstance(body.get("list"), list) and body["list"]:
            first = body["list"][0]
            if isinstance(first, dict) and first.get("ret") is not None:
                error_code = int(first.get("ret") or 0)
        elif base_response.get("ret") is not None:
            error_code = int(base_response.get("ret") or 0)

        error_message = ""
        if body.get("error_message") is not None:
            error_message = str(body.get("error_message") or "")
        elif base_response.get("errMsg") is not None:
            error_message = str(base_response.get("errMsg") or "")
        elif body.get("errMsg") is not None:
            error_message = str(body.get("errMsg") or "")

        return JuheApiResponse(
            error_code=error_code,
            error_message=error_message,
            data=body.get("data"),
            raw=body,
        )

    def _resolve_public_url(self) -> str:
        if not self.public_base_url:
            return self._public_url
        return self.public_base_url.rstrip("/") + "/open/GuidRequest"

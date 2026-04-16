from __future__ import annotations

import asyncio
import json
import random
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any, Protocol

from .exceptions import QwSaasRequestError, QwSaasResponseError

DEFAULT_WS_URL = "wss://chat-api.juhebot.com/ws/juwe"


class JsonTransport(Protocol):
    @property
    def closed(self) -> bool: ...

    async def send_json(self, payload: dict[str, Any]) -> None: ...

    async def receive_json(self) -> dict[str, Any]: ...

    async def close(self) -> None: ...


TransportFactory = Callable[[str, float], Awaitable[JsonTransport]]


class AiohttpJsonTransport:
    def __init__(self, session: Any, ws: Any) -> None:
        self._session = session
        self._ws = ws

    @property
    def closed(self) -> bool:
        return bool(self._ws.closed)

    async def send_json(self, payload: dict[str, Any]) -> None:
        await self._ws.send_json(payload)

    async def receive_json(self) -> dict[str, Any]:
        try:
            import aiohttp
        except ImportError as exc:  # pragma: no cover - import guarded by factory
            raise QwSaasRequestError("aiohttp is required for WebSocket support") from exc

        message = await self._ws.receive()
        if message.type == aiohttp.WSMsgType.TEXT:
            try:
                payload = json.loads(message.data)
            except (TypeError, ValueError) as exc:
                raise QwSaasResponseError("Invalid JSON WebSocket payload") from exc
            if not isinstance(payload, dict):
                raise QwSaasResponseError("Unexpected WebSocket payload type")
            return payload
        if message.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.CLOSE, aiohttp.WSMsgType.ERROR):
            raise QwSaasResponseError("Juhe WebSocket closed")
        raise QwSaasResponseError(f"Unsupported WebSocket message type: {message.type}")

    async def close(self) -> None:
        if not self._ws.closed:
            await self._ws.close()
        if not self._session.closed:
            await self._session.close()


async def default_transport_factory(url: str, heartbeat_seconds: float) -> JsonTransport:
    try:
        import aiohttp
    except ImportError as exc:
        raise QwSaasRequestError("aiohttp is required for WebSocket support") from exc

    session = aiohttp.ClientSession()
    try:
        ws = await session.ws_connect(url, heartbeat=heartbeat_seconds)
    except Exception:
        await session.close()
        raise
    return AiohttpJsonTransport(session, ws)


@dataclass
class JuheWsClient:
    app_key: str
    app_secret: str
    guid: str
    ws_url: str = DEFAULT_WS_URL
    heartbeat_seconds: float = 30.0
    reconnect_backoff_seconds: tuple[float, ...] = (2.0, 5.0, 10.0, 30.0, 60.0)
    jitter_seconds: float = 0.5
    transport_factory: TransportFactory | None = None

    _transport: JsonTransport | None = field(default=None, init=False, repr=False)
    _running: bool = field(default=False, init=False, repr=False)

    async def connect(self) -> JsonTransport:
        if not self.app_key:
            raise QwSaasRequestError("app_key is required")
        if not self.app_secret:
            raise QwSaasRequestError("app_secret is required")
        if not self.guid:
            raise QwSaasRequestError("guid is required")

        if self._transport and not self._transport.closed:
            return self._transport

        factory = self.transport_factory or default_transport_factory
        self._transport = await factory(self.ws_url, self.heartbeat_seconds)
        await self.send_auth()
        return self._transport

    async def send_auth(self) -> None:
        transport = await self.connect()
        await transport.send_json(
            {
                "type": "auth",
                "app_key": self.app_key,
                "app_secret": self.app_secret,
                "guid": self.guid,
            }
        )

    async def ack(self, event_id: Any, success: bool) -> None:
        transport = await self.connect()
        await transport.send_json({"type": "ack", "event_id": event_id, "success": success})

    async def receive(self) -> dict[str, Any]:
        transport = await self.connect()
        return await transport.receive_json()

    async def close(self) -> None:
        self._running = False
        await self._close_transport()

    def stop(self) -> None:
        self._running = False

    async def listen_forever(self, handler: Callable[[dict[str, Any]], Awaitable[None]]) -> None:
        self._running = True
        backoff_index = 0
        while self._running:
            try:
                payload = await self.receive()
                backoff_index = 0
                await handler(payload)
            except asyncio.CancelledError:
                raise
            except Exception:
                if not self._running:
                    break
                await self._close_transport()
                delay = self._compute_backoff_delay(backoff_index)
                backoff_index = min(backoff_index + 1, len(self.reconnect_backoff_seconds) - 1)
                await asyncio.sleep(delay)

    async def _close_transport(self) -> None:
        if self._transport is not None:
            await self._transport.close()
            self._transport = None

    def _compute_backoff_delay(self, backoff_index: int) -> float:
        if not self.reconnect_backoff_seconds:
            return 0.0
        base_delay = self.reconnect_backoff_seconds[min(backoff_index, len(self.reconnect_backoff_seconds) - 1)]
        if self.jitter_seconds <= 0:
            return base_delay
        return base_delay + random.uniform(0, self.jitter_seconds)

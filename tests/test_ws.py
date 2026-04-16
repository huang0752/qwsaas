from __future__ import annotations

from typing import Any

import pytest

import qwsaas.ws as ws_module
from qwsaas.ws import JuheWsClient


class FakeTransport:
    def __init__(self, incoming: list[Any] | None = None) -> None:
        self.incoming = incoming or []
        self.sent: list[dict[str, Any]] = []
        self.closed = False

    async def send_json(self, payload: dict[str, Any]) -> None:
        self.sent.append(payload)

    async def receive_json(self) -> dict[str, Any]:
        item = self.incoming.pop(0)
        if isinstance(item, Exception):
            raise item
        return item

    async def close(self) -> None:
        self.closed = True


@pytest.mark.asyncio
async def test_connect_sends_auth_payload() -> None:
    transport = FakeTransport()

    async def factory(url: str, heartbeat: float) -> FakeTransport:
        assert url == "wss://example.test/ws"
        assert heartbeat == 30.0
        return transport

    client = JuheWsClient(
        app_key="app",
        app_secret="secret",
        guid="guid-1",
        ws_url="wss://example.test/ws",
        transport_factory=factory,
    )

    await client.connect()

    assert transport.sent == [
        {"type": "auth", "app_key": "app", "app_secret": "secret", "guid": "guid-1"}
    ]


@pytest.mark.asyncio
async def test_ack_sends_expected_payload() -> None:
    transport = FakeTransport()

    async def factory(url: str, heartbeat: float) -> FakeTransport:
        return transport

    client = JuheWsClient(
        app_key="app",
        app_secret="secret",
        guid="guid-1",
        transport_factory=factory,
    )

    await client.connect()
    await client.ack("evt-1", True)

    assert transport.sent[-1] == {"type": "ack", "event_id": "evt-1", "success": True}


@pytest.mark.asyncio
async def test_listen_forever_reconnects_with_configured_backoff(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first = FakeTransport([RuntimeError("boom")])
    second = FakeTransport([{"type": "callback", "event_id": "evt-1"}])
    transports = iter([first, second])
    sleeps: list[float] = []
    received: list[dict[str, Any]] = []

    async def factory(url: str, heartbeat: float) -> FakeTransport:
        return next(transports)

    async def fake_sleep(delay: float) -> None:
        sleeps.append(delay)

    client = JuheWsClient(
        app_key="app",
        app_secret="secret",
        guid="guid-1",
        transport_factory=factory,
        reconnect_backoff_seconds=(2.0, 5.0),
        jitter_seconds=0.0,
    )

    async def handler(payload: dict[str, Any]) -> None:
        received.append(payload)
        client.stop()

    monkeypatch.setattr(ws_module.asyncio, "sleep", fake_sleep)

    await client.listen_forever(handler)

    assert first.closed is True
    assert sleeps == [2.0]
    assert received == [{"type": "callback", "event_id": "evt-1"}]

"""Real PostgreSQL checks enabled explicitly against a disposable fixture."""

import os
import socket
from time import monotonic

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from lib_management.config import Settings
from lib_management.main import create_app

pytestmark = pytest.mark.skipif(
    os.environ.get("RUN_DB_INTEGRATION") != "1",
    reason="Set RUN_DB_INTEGRATION=1 with a disposable PostgreSQL fixture",
)


def test_real_select_and_readiness():
    with TestClient(create_app(Settings())) as client:
        with client.app.state.engine.connect() as connection:
            assert connection.execute(text("SELECT 1")).scalar_one() == 1
        response = client.get("/health/ready")
        assert response.status_code == 200
        assert response.json() == {"status": "ready"}


def test_wrong_password_is_bounded_and_preserves_liveness():
    settings = Settings(
        **(Settings().model_dump() | {"db_password": "deliberately-wrong-ci-password"})
    )
    with TestClient(create_app(settings)) as client:
        started = monotonic()
        response = client.get("/health/ready")
        assert monotonic() - started < 5
        assert response.status_code == 503
        assert response.json() == {"status": "not_ready"}
        assert settings.db_password.get_secret_value() not in response.text
        assert client.get("/health/live").status_code == 200


def test_closed_port_is_bounded_and_preserves_liveness():
    # Bound, non-listening socket prevents another process taking this port.
    with socket.socket() as closed_port:
        closed_port.bind(("127.0.0.1", 0))
        settings = Settings(
            **(
                Settings().model_dump()
                | {"db_host": "127.0.0.1", "db_port": closed_port.getsockname()[1]}
            )
        )
        with TestClient(create_app(settings)) as client:
            started = monotonic()
            response = client.get("/health/ready")
            assert monotonic() - started < 5
            assert response.status_code == 503
            assert response.json() == {"status": "not_ready"}
            assert client.get("/health/live").status_code == 200


def test_established_connection_blackhole_concurrency():
    """TCP proxy completes auth then discards SELECT responses without EOF."""
    import asyncio

    import httpx

    from lib_management.db import DatabaseProbe

    async def scenario():
        settings = Settings()
        blackhole = False
        stalled = 0
        handlers = set()

        async def proxy(reader, writer):
            nonlocal stalled
            task = asyncio.current_task()
            handlers.add(task)
            upstream = None
            try:
                upstream_reader, upstream = await asyncio.open_connection(
                    settings.db_host, settings.db_port
                )
                dropping = False

                async def forward_client():
                    nonlocal dropping, stalled
                    while data := await reader.read(65536):
                        if blackhole and b"SELECT 1" in data:
                            dropping = True
                            stalled += 1
                        upstream.write(data)
                        await upstream.drain()

                async def forward_server():
                    while data := await upstream_reader.read(65536):
                        if not dropping:
                            writer.write(data)
                            await writer.drain()

                tasks = [
                    asyncio.create_task(forward_client()),
                    asyncio.create_task(forward_server()),
                ]
                try:
                    await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
                finally:
                    for child in tasks:
                        child.cancel()
                    await asyncio.gather(*tasks, return_exceptions=True)
            finally:
                writer.close()
                if upstream is not None:
                    upstream.close()
                handlers.discard(task)

        server = await asyncio.start_server(proxy, "127.0.0.1", 0)
        port = server.sockets[0].getsockname()[1]
        proxy_settings = Settings(
            **(settings.model_dump() | {"db_host": "127.0.0.1", "db_port": port})
        )
        probe = DatabaseProbe(proxy_settings)
        app = create_app(proxy_settings)
        app.state.db_probe = probe
        try:
            assert await probe.check() is True
            blackhole = True
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="http://test"
            ) as client:
                started = asyncio.get_running_loop().time()
                requests = [
                    asyncio.create_task(client.get("/health/ready")) for _ in range(12)
                ]
                await asyncio.sleep(0.15)
                live = await asyncio.wait_for(client.get("/health/live"), 0.25)
                assert live.status_code == 200
                responses = await asyncio.gather(*requests)
                assert all(response.status_code == 503 for response in responses)
                assert asyncio.get_running_loop().time() - started < 2.5
            assert stalled == 4
            assert probe.slots._value == 4
            blackhole = False
            assert await probe.check() is True
        finally:
            server.close()
            await server.wait_closed()
            for handler in tuple(handlers):
                handler.cancel()
            await asyncio.gather(*handlers, return_exceptions=True)

    asyncio.run(scenario())


def test_readiness_does_not_wait_for_business_engine_pool():
    from contextlib import ExitStack

    with TestClient(create_app(Settings())) as client, ExitStack() as connections:
        engine = client.app.state.engine
        # Exhaust the default engine's five persistent + ten overflow slots.
        for _ in range(15):
            connections.enter_context(engine.connect())
        started = monotonic()
        assert client.get("/health/ready").status_code == 200
        assert monotonic() - started < 2.5
        assert client.get("/health/live").status_code == 200

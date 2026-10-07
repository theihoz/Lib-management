"""Deadline and cleanup regression checks."""

import asyncio
from unittest.mock import AsyncMock, patch

import httpx

from lib_management.config import Settings
from lib_management.db import DatabaseProbe
from lib_management.main import create_app


def test_read_stall_closes_before_cancellation():
    async def scenario():
        closed = asyncio.Event()
        cancelled = asyncio.Event()
        connection = AsyncMock()

        async def execute(*args):
            try:
                await asyncio.Event().wait()
            except asyncio.CancelledError:
                assert closed.is_set()
                cancelled.set()
                raise

        async def close():
            closed.set()

        connection.execute.side_effect = execute
        connection.close.side_effect = close
        probe = DatabaseProbe(Settings(db_password="fixture"), timeout=0.05)
        with patch(
            "lib_management.db.psycopg.AsyncConnection.connect", return_value=connection
        ):
            assert await probe.check() is False
        assert cancelled.is_set()
        assert probe.slots._value == 4
        connection.close.assert_awaited_once()

    asyncio.run(scenario())


def test_concurrency_bounds_admission_and_preserves_liveness():
    async def scenario():
        active = 0
        peak = 0

        async def connect(**kwargs):
            nonlocal active, peak
            active += 1
            peak = max(peak, active)
            try:
                await asyncio.Event().wait()
            finally:
                active -= 1

        settings = Settings(db_password="fixture")
        app = create_app(settings)
        probe = DatabaseProbe(settings, timeout=0.1)
        app.state.db_probe = probe
        with patch(
            "lib_management.db.psycopg.AsyncConnection.connect", side_effect=connect
        ):
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="http://test"
            ) as client:
                started = asyncio.get_running_loop().time()
                requests = [
                    asyncio.create_task(client.get("/health/ready")) for _ in range(40)
                ]
                await asyncio.sleep(0.02)
                live = await asyncio.wait_for(client.get("/health/live"), timeout=0.05)
                assert live.status_code == 200
                responses = await asyncio.gather(*requests)
                assert all(response.status_code == 503 for response in responses)
                assert asyncio.get_running_loop().time() - started < 0.5
        assert peak == 4
        assert active == 0
        assert probe.slots._value == 4

    asyncio.run(scenario())


def test_request_cancellation_closes_connection():
    async def scenario():
        entered = asyncio.Event()
        closed = asyncio.Event()
        connection = AsyncMock()

        async def execute(*args):
            entered.set()
            try:
                await asyncio.Event().wait()
            except asyncio.CancelledError:
                assert closed.is_set()
                raise

        async def close():
            closed.set()

        connection.execute.side_effect = execute
        connection.close.side_effect = close
        probe = DatabaseProbe(Settings(db_password="fixture"))
        with patch(
            "lib_management.db.psycopg.AsyncConnection.connect", return_value=connection
        ):
            task = asyncio.create_task(probe.check())
            await entered.wait()
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        assert closed.is_set()
        assert probe.slots._value == 4

    asyncio.run(scenario())

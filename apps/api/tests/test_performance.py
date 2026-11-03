"""Performance contracts: compression, cache privacy and bounded reuse."""

from concurrent.futures import ThreadPoolExecutor
from threading import Event

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.responses import JSONResponse

from lib_management import performance


def test_install_performance_compresses_large_api_payload_and_blocks_shared_cache():
    app = FastAPI()
    performance.install_performance(app)

    @app.get("/api/v1/example")
    def example():
        return {"items": ["a" * 120] * 30}

    response = TestClient(app).get(
        "/api/v1/example", headers={"Accept-Encoding": "gzip"}
    )
    assert response.status_code == 200
    assert response.headers["content-encoding"] == "gzip"
    assert response.headers["cache-control"] == "private, no-store"
    assert "Accept-Encoding" in response.headers["vary"]
    assert response.json() == {"items": ["a" * 120] * 30}


def test_install_performance_preserves_existing_vary_and_small_payloads():
    app = FastAPI()
    performance.install_performance(app)

    @app.get("/api/v1/small")
    def small():
        return JSONResponse({"ok": True}, headers={"Vary": "Origin"})

    response = TestClient(app).get("/api/v1/small", headers={"Accept-Encoding": "gzip"})
    assert "content-encoding" not in response.headers
    assert response.headers["vary"] == "Origin"
    assert response.headers["cache-control"] == "private, no-store"


def test_public_read_cache_reuses_and_expires_results():
    now = [0.0]
    calls = 0
    cache = performance.PublicReadCache[str](ttl_seconds=5, clock=lambda: now[0])

    def compute():
        nonlocal calls
        calls += 1
        return f"value-{calls}"

    assert cache.get_or_compute("reference", compute) == "value-1"
    now[0] = 4.9
    assert cache.get_or_compute("reference", compute) == "value-1"
    now[0] = 5.0
    assert cache.get_or_compute("reference", compute) == "value-2"


def test_public_read_cache_evicts_least_recently_used_and_copies_mutable_results():
    cache = performance.PublicReadCache[list[str]](max_entries=2)
    original = ["original"]
    result = cache.get_or_compute("first", lambda: original)
    result.append("caller mutation")
    original.append("producer mutation")
    cache.get_or_compute("second", lambda: ["second"])
    assert cache.get_or_compute("first", lambda: ["unexpected"]) == ["original"]
    cache.get_or_compute("third", lambda: ["third"])
    assert cache.get_or_compute("second", lambda: ["recomputed"]) == ["recomputed"]


def test_public_read_cache_invalidates_in_flight_computation():
    cache = performance.PublicReadCache[str]()
    started, finish = Event(), Event()

    def slow():
        started.set()
        assert finish.wait(timeout=5)
        return "stale"

    with ThreadPoolExecutor(max_workers=1) as executor:
        result = executor.submit(cache.get_or_compute, "key", slow)
        assert started.wait(timeout=5)
        cache.invalidate()
        finish.set()
        assert result.result(timeout=5) == "stale"
    assert cache.get_or_compute("key", lambda: "fresh") == "fresh"


def test_public_read_cache_does_not_cache_failed_computation():
    cache = performance.PublicReadCache[str]()

    def fail():
        raise ValueError("failed computation")

    with pytest.raises(ValueError):
        cache.get_or_compute("key", fail)
    assert cache.get_or_compute("key", lambda: "success") == "success"


@pytest.mark.parametrize("options", [{"max_entries": 0}, {"ttl_seconds": 0}])
def test_public_read_cache_rejects_unbounded_or_immediate_expiry(options):
    with pytest.raises(ValueError):
        performance.PublicReadCache(**options)

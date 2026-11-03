"""Response compression and explicit, public-only computation memoization.

No authenticated endpoint uses PublicReadCache. Its caller must establish that
both keys and values are public, contain no PII, and never vary by permissions.
"""

from collections import OrderedDict
from collections.abc import Callable, Hashable
from copy import deepcopy
from math import isfinite
from threading import Lock
from time import monotonic

from fastapi import FastAPI
from starlette.datastructures import MutableHeaders
from starlette.middleware.gzip import GZipMiddleware
from starlette.types import ASGIApp, Message, Receive, Scope, Send


class PrivateApiCacheControlMiddleware:
    """Prevent browser/shared HTTP caches from storing business API responses."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        path = scope.get("path", "")
        if scope["type"] != "http" or not (path == "/api" or path.startswith("/api/")):
            await self.app(scope, receive, send)
            return

        async def send_private(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                headers["Cache-Control"] = "private, no-store"
            await send(message)

        await self.app(scope, receive, send_private)


def install_performance(app: FastAPI) -> None:
    """Install once at app construction, before requests or startup."""
    app.add_middleware(GZipMiddleware, minimum_size=1024, compresslevel=5)
    app.add_middleware(PrivateApiCacheControlMiddleware)


class PublicReadCache[T]:
    """Bounded, process-local TTL/LRU cache for public non-PII computations.

    Mutable results are copied so callers cannot change cached state. Misses
    compute outside the lock; concurrent misses may duplicate work. invalidate()
    prevents an earlier in-flight result from repopulating cleared state. It
    cannot revoke a result already being returned to an in-flight caller.

    A replica's invalidation cannot reach another process. Do not use for DB
    business records, sessions, permission checks or any private response.
    """

    def __init__(
        self,
        *,
        max_entries: int = 128,
        ttl_seconds: float = 15,
        clock: Callable[[], float] = monotonic,
    ) -> None:
        if max_entries < 1 or ttl_seconds <= 0 or not isfinite(ttl_seconds):
            raise ValueError("Cache capacity and finite TTL must be positive")
        self._max_entries = max_entries
        self._ttl_seconds = ttl_seconds
        self._clock = clock
        self._entries: OrderedDict[Hashable, tuple[float, T]] = OrderedDict()
        self._generation = 0
        self._lock = Lock()

    def get_or_compute(self, key: Hashable, compute: Callable[[], T]) -> T:
        """Memoize a public computation, leaving exceptions uncached."""
        with self._lock:
            now = self._clock()
            cached = self._entries.get(key)
            if cached is not None and now < cached[0]:
                self._entries.move_to_end(key)
                return deepcopy(cached[1])
            self._entries.pop(key, None)
            generation = self._generation

        value = compute()
        snapshot = deepcopy(value)
        with self._lock:
            if generation == self._generation:
                self._entries[key] = (self._clock() + self._ttl_seconds, snapshot)
                self._entries.move_to_end(key)
                while len(self._entries) > self._max_entries:
                    self._entries.popitem(last=False)
        return value

    def invalidate(self) -> None:
        """Clear this process after the underlying public inputs change."""
        with self._lock:
            self._generation += 1
            self._entries.clear()

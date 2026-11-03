"""X-Request-ID propagation as a pure ASGI middleware."""

import re
import uuid
from contextvars import ContextVar

from starlette.types import ASGIApp, Message, Receive, Scope, Send

HEADER = "x-request-id"
_VALID = re.compile(r"^[A-Za-z0-9-]{8,100}$")
_current: ContextVar[str | None] = ContextVar("request_id", default=None)


def current_request_id() -> str | None:
    return _current.get()


def accept_or_generate(candidate: str | None) -> str:
    if candidate is not None and _VALID.fullmatch(candidate):
        return candidate
    return str(uuid.uuid4())


class RequestIdMiddleware:
    """Accepts a well-formed client ID or generates one; echoes it back."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        raw = dict(scope.get("headers", [])).get(HEADER.encode())
        request_id = accept_or_generate(raw.decode("latin-1") if raw else None)
        scope.setdefault("state", {})["request_id"] = request_id

        async def send_with_id(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = [
                    (k, v)
                    for k, v in message.get("headers", [])
                    if k != HEADER.encode()
                ]
                headers.append((HEADER.encode(), request_id.encode()))
                message["headers"] = headers
            await send(message)

        token = _current.set(request_id)
        try:
            await self.app(scope, receive, send_with_id)
        finally:
            _current.reset(token)

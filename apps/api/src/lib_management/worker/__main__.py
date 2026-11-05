"""``python -m lib_management.worker``: poll loop, clean stop on SIGTERM."""

import logging
import os
import signal
import socket
import threading
import time
from typing import Any

from lib_management.config import Settings
from lib_management.db import create_engine_from_settings, create_session_factory
from lib_management.worker.dispatcher import dispatch_once
from lib_management.worker.registry import default_registry
from lib_management.worker.runner import Runner

POLL_SECONDS = 1.0
SWEEP_SECONDS = 60.0


def sweep(session_factory: Any) -> int:
    """C07 / Lab 3 Job RESERVATION_EXPIRY: expire READY holds past their deadline."""
    from lib_management.circulation.router import expire_ready_reservations

    with session_factory() as session, session.begin():
        return expire_ready_reservations(session)


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    settings = Settings()
    engine = create_engine_from_settings(settings)
    session_factory = create_session_factory(engine)
    registry = default_registry()
    runner = Runner(
        session_factory,
        registry,
        owner=f"{socket.gethostname()}:{os.getpid()}",
        lease_seconds=settings.worker_lease_seconds,
        max_attempts=settings.worker_max_attempts,
    )
    stop = threading.Event()
    for signum in (signal.SIGTERM, signal.SIGINT):
        signal.signal(signum, lambda *_: stop.set())
    logging.getLogger(__name__).info("Worker started as %s", runner.owner)
    last_sweep = 0.0
    try:
        while not stop.is_set():
            if time.monotonic() - last_sweep >= SWEEP_SECONDS:
                last_sweep = time.monotonic()
                try:
                    if expired := sweep(session_factory):
                        logging.getLogger(__name__).info(
                            "Expired %d reservations", expired
                        )
                except Exception:
                    logging.getLogger(__name__).exception("Reservation sweep failed")
            try:
                dispatched = dispatch_once(session_factory, registry)
                ran = runner.run_once()
            except Exception:
                logging.getLogger(__name__).exception("Worker iteration failed")
                dispatched, ran = 0, False
            if not dispatched and not ran:
                stop.wait(POLL_SECONDS)
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()

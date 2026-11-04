"""Allowlist of event consumers and job handlers."""

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import Any


class JobError(Exception):
    """Handler failure with a short, secret-free error code."""

    def __init__(self, code: str, *, permanent: bool = False) -> None:
        super().__init__(code)
        self.code = code[:100]
        self.permanent = permanent


@dataclass(frozen=True)
class JobContext:
    job_id: str
    job_type: str
    attempt: int
    payload: Mapping[str, Any]
    heartbeat: Callable[[], bool]
    """Extends the lease; returns False if the lease was lost (stop work)."""


Handler = Callable[[JobContext], None]


@dataclass(frozen=True)
class Consumer:
    name: str
    job_type: str


@dataclass(frozen=True)
class Registry:
    handlers: Mapping[str, Handler] = field(default_factory=dict)
    consumers: Mapping[str, tuple[Consumer, ...]] = field(default_factory=dict)

    def consumers_for(self, event_type: str) -> tuple[Consumer, ...]:
        return self.consumers.get(event_type, ())


def noop(context: JobContext) -> None:
    """Test handler proving the pipeline end to end."""


def default_registry() -> Registry:
    from lib_management.models import load_all_models
    from lib_management.reporting.handlers import configured_handler

    # Handlers flush rows (audit_log, outbox) with FKs into other modules' tables;
    # unlike the API, the worker process imports no routers, so load them all here.
    load_all_models()

    return Registry(
        handlers={
            "noop.v1": noop,
            "report": configured_handler,
            "export": configured_handler,
        }
    )

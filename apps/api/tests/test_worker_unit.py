import random

from lib_management.worker.runner import backoff_seconds


def test_backoff_doubles_and_caps():
    rng = random.Random(0)
    bases = [1, 2, 4, 8, 16, 32, 60, 60]
    for attempt, base in enumerate(bases, start=1):
        value = backoff_seconds(attempt, rng)
        assert base <= value <= min(base * 1.25, 60)


def test_default_registry_loads_every_model_in_a_fresh_process():
    # The worker imports no routers; without load_all_models a handler flush
    # failed with NoReferencedTableError (audit_log.actor_id -> account).
    import subprocess
    import sys

    code = (
        "from lib_management.worker.registry import default_registry\n"
        "from lib_management.models import Base\n"
        "default_registry()\n"
        "Base.metadata.sorted_tables\n"
        "assert 'account' in Base.metadata.tables\n"
    )
    subprocess.run([sys.executable, "-c", code], check=True)

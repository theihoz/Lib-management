import random

from lib_management.worker.runner import backoff_seconds


def test_backoff_doubles_and_caps():
    rng = random.Random(0)
    bases = [1, 2, 4, 8, 16, 32, 60, 60]
    for attempt, base in enumerate(bases, start=1):
        value = backoff_seconds(attempt, rng)
        assert base <= value <= min(base * 1.25, 60)

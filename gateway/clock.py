"""Injectable clock so tests and demos can fast-forward time (budget windows, seal expiry)."""
import time

_offset = 0.0


def now() -> float:
    return time.time() + _offset


def advance(seconds: float) -> None:
    global _offset
    _offset += seconds


def reset() -> None:
    global _offset
    _offset = 0.0

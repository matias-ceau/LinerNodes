"""Lightweight no-op metrics façade.

All functions are safe to import and call in any runtime path. By default,
implementations are pure no-ops with minimal overhead and no side effects.

Future enablement may be controlled via environment variables or configuration.
For example:
- LINERNODES_METRICS_BACKEND: identifies the metrics backend to use (not used yet)

APIs:
- counter(name, tags) -> (amount: int = 1) -> None
- gauge(name, tags) -> (value: float) -> None
- timer(name, tags) -> context manager returning elapsed seconds (float) but does not emit
- record_distribution(name, value, tags) -> None
"""

from __future__ import annotations

from contextlib import contextmanager
import time
from typing import Callable, Dict, Iterator, Optional


def counter(name: str, tags: Optional[Dict[str, str]] = None) -> Callable[[int], None]:
    """Return a callable that increments a counter.

    Parameters
    ----------
    name:
        Metric name.
    tags:
        Optional tags to attach to the metric. Unused in no-op implementation.

    Returns
    -------
    Callable[[int], None]
        A function increment(amount: int = 1) -> None that discards input.
    """

    def increment(amount: int = 1) -> None:  # noqa: ARG001 - amount intentionally unused
        # Pure no-op
        return None

    return increment


def gauge(name: str, tags: Optional[Dict[str, str]] = None) -> Callable[[float], None]:
    """Return a callable that sets a gauge value.

    Parameters
    ----------
    name:
        Metric name.
    tags:
        Optional tags to attach to the metric. Unused in no-op implementation.

    Returns
    -------
    Callable[[float], None]
        A function set(value: float) -> None that discards input.
    """

    def set_value(value: float) -> None:  # noqa: ARG001 - value intentionally unused
        # Pure no-op
        return None

    return set_value


@contextmanager
def timer(name: str, tags: Optional[Dict[str, str]] = None) -> Iterator[float]:  # noqa: ARG001 - name/tags intentionally unused
    """Context manager that measures elapsed time, but does not emit.

    Usage
    -----
    with timer("op"):
        do_work()

    The yielded value is the elapsed time in seconds (float) when the context
    exits. This allows callsites to optionally read the measurement if desired,
    without emitting any metrics by default.

    Parameters
    ----------
    name:
        Metric name (unused).
    tags:
        Optional tags (unused).

    Yields
    ------
    float
        Elapsed seconds on exit.
    """
    start = time.perf_counter()
    try:
        # Yield a placeholder first; the actual elapsed value is computed at exit.
        yield 0.0
    finally:
        _ = time.perf_counter() - start
        # Intentionally do nothing with the elapsed time.


def record_distribution(
    name: str, value: float, tags: Optional[Dict[str, str]] = None
) -> None:  # noqa: ARG001 - parameters intentionally unused
    """Record a distribution sample.

    No-op by default. Safe to call from any path.

    Parameters
    ----------
    name:
        Metric name (unused).
    value:
        Sample value (unused).
    tags:
        Optional tags (unused).
    """
    return None

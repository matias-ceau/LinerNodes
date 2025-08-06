"""Lightweight retry decorator scaffold (no external dependencies).

Behavior
--------
- If tries == 1 (default), execute the function directly with minimal overhead.
- If tries > 1, perform a simple retry loop with optional delay between attempts.
- On failure after all attempts, re-raise the last exception.
- Only logs at DEBUG level using centralized logging; silent otherwise.

Notes
-----
- TODO: Add jitter/backoff strategy and cancellation support in a future phase.
- Keep stdlib-only and import-safe.
"""

from __future__ import annotations

import time
from functools import wraps
from typing import Any, Callable, Tuple, Type, TypeVar

try:
    # Centralized logger pattern
    from linernodes.logging.setup import get_logger
except Exception:  # pragma: no cover
    def get_logger(name: str):  # type: ignore[no-redef]
        """Fallback logger returning a stdlib logger with debug method."""
        import logging as _fallback_logging
        logger = _fallback_logging.getLogger(name)
        # ensure it has at least a null handler to avoid 'No handler' warnings
        if not logger.handlers:
            logger.addHandler(_fallback_logging.NullHandler())
        return logger


F = TypeVar("F", bound=Callable[..., Any])


def retry(
    tries: int = 1,
    delay: float = 0.0,
    backoff: float = 1.0,
    retry_on: Tuple[Type[BaseException], ...] = (Exception,),
) -> Callable[[F], F]:
    """Retry decorator with low overhead defaults.

    Parameters
    ----------
    tries:
        Total attempts to make. If 1, call-through with no loop.
    delay:
        Initial sleep duration between attempts (seconds). Only used if tries > 1.
    backoff:
        Multiplicative factor applied to delay after each failed attempt
        (currently unused, reserved for future improvement).
    retry_on:
        Exception types that trigger a retry.

    Returns
    -------
    Callable[[F], F]
        Decorated function.

    Notes
    -----
    - Logging occurs at debug level via centralized logger and is silent otherwise.
    - TODO: Implement jitter/backoff strategy and cancellation support.
    """
    logger = get_logger(__name__)

    if tries <= 1:
        # Fast path: no additional overhead beyond one closure and one call.
        def _decorator_fast(func: F) -> F:
            @wraps(func)
            def wrapper(*args: Any, **kwargs: Any):  # type: ignore[misc]
                return func(*args, **kwargs)

            return wrapper  # type: ignore[return-value]

        return _decorator_fast

    # Retry loop path
    def _decorator_retry(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any):  # type: ignore[misc]
            attempt = 0
            current_delay = float(delay)
            while True:
                try:
                    attempt += 1
                    return func(*args, **kwargs)
                except retry_on as exc:  # type: ignore[misc]
                    if attempt >= tries:
                        logger.debug(
                            "retry: giving up after %s/%s attempts on %s",
                            attempt,
                            tries,
                            func.__name__,
                        )
                        raise
                    logger.debug(
                        "retry: attempt %s/%s failed (%s), retrying after %.3fs",
                        attempt,
                        tries,
                        exc.__class__.__name__,
                        current_delay,
                    )
                    if current_delay > 0:
                        time.sleep(current_delay)
                    # TODO: consider applying backoff and jitter here in a future phase
                    # Keep constant delay for now to avoid behavioral changes.
                    # current_delay *= backoff
                    continue

        return wrapper  # type: ignore[return-value]

    return _decorator_retry

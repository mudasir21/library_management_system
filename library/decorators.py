"""Decorators Module.

Implements reusable decorators satisfying Section 3.2 requirements.
Includes an audit logging decorator that records operation lifecycle,
arguments, elapsed time, and errors using Python's logging module.
"""

from __future__ import annotations

import functools
import logging
import time
from typing import Any, Callable, TypeVar

F = TypeVar("F", bound=Callable[..., Any])
logger = logging.getLogger("library.audit")


def audit_log(action_name: str | None = None) -> Callable[[F], F]:
    """Decorator to audit and log service-level operations.

    Records invocation start, parameters, successful completion, execution duration,
    and any raised domain exceptions.

    Args:
        action_name: Optional human-readable action label. Defaults to function name.

    Returns:
        Decorated function.
    """

    def decorator(func: F) -> F:
        label = action_name or func.__name__

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Build safe parameter preview omitting self
            call_args = args[1:] if args and hasattr(args[0], "__class__") else args
            arg_str = ", ".join([repr(a) for a in call_args] + [f"{k}={v!r}" for k, v in kwargs.items()])

            logger.info("ACTION_START | %s | args=(%s)", label, arg_str)
            start_time = time.perf_counter()

            try:
                result = func(*args, **kwargs)
                duration_ms = (time.perf_counter() - start_time) * 1000.0
                logger.info(
                    "ACTION_SUCCESS | %s | duration=%.2fms",
                    label,
                    duration_ms,
                )
                return result
            except Exception as exc:
                duration_ms = (time.perf_counter() - start_time) * 1000.0
                logger.warning(
                    "ACTION_FAILED | %s | duration=%.2fms | error=%s: %s",
                    label,
                    duration_ms,
                    exc.__class__.__name__,
                    str(exc),
                )
                raise

        return wrapper  # type: ignore[return-value]

    return decorator

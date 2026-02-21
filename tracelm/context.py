"""Execution context helpers for trace and span tracking.

This module uses ``contextvars`` so trace/span state is isolated per execution
context (thread, task, coroutine) and does not leak across concurrent work.
"""

from __future__ import annotations

from contextvars import ContextVar, Token
from typing import Any
from uuid import uuid4

# Context-local holders for active trace and span.
_current_trace: ContextVar[str | None] = ContextVar("current_trace", default=None)
_current_span: ContextVar[Any | None] = ContextVar("current_span", default=None)


def create_new_trace() -> str:
    """Create and set a new trace ID for the current context.

    Returns:
        A unique trace identifier.
    """
    trace_id = uuid4().hex
    _current_trace.set(trace_id)
    # New traces start without an active span by default.
    _current_span.set(None)
    return trace_id


def get_current_trace() -> str | None:
    """Return the active trace ID for the current context, if any."""
    return _current_trace.get()


def set_current_span(span: Any | None) -> Token[Any | None]:
    """Set the active span for the current context.

    Args:
        span: Span-like object to mark as active, or ``None`` to clear.

    Returns:
        A context token that can be used with ``_current_span.reset(token)``
        by advanced callers that need scoped restoration.
    """
    return _current_span.set(span)


def get_current_span() -> Any | None:
    """Return the active span for the current context, if any."""
    return _current_span.get()


def record_tokens(tokens_in: int = 0, tokens_out: int = 0, cost: float = 0.0) -> None:
    """Accumulate token and cost metrics on the current active span.

    If no span is active, this function does nothing.
    """
    span = get_current_span()
    if span is None:
        return

    try:
        span.tokens_in += int(tokens_in)
        span.tokens_out += int(tokens_out)
        span.cost += float(cost)
    except Exception:
        return

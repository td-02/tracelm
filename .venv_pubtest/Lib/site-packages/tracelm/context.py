"""Execution context helpers for trace and span tracking.

This module uses ``contextvars`` so trace/span state is isolated per execution
context (thread, task, coroutine) and does not leak across concurrent work.
"""

from __future__ import annotations

import secrets
from contextvars import ContextVar, Token
from typing import Any

_current_trace: ContextVar[str | None] = ContextVar("current_trace", default=None)
_current_span: ContextVar[Any | None] = ContextVar("current_span", default=None)


def generate_trace_id() -> str:
    while True:
        trace_id = secrets.token_hex(16).lower()
        if trace_id != "0" * 32:
            return trace_id


def generate_span_id() -> str:
    while True:
        span_id = secrets.token_hex(8).lower()
        if span_id != "0" * 16:
            return span_id


def create_new_trace() -> str:
    trace_id = generate_trace_id()
    _current_trace.set(trace_id)
    _current_span.set(None)
    return trace_id


def get_current_trace() -> str | None:
    return _current_trace.get()


def set_current_span(span: Any | None) -> Token[Any | None]:
    return _current_span.set(span)


def get_current_span() -> Any | None:
    return _current_span.get()


def record_tokens(tokens_in: int = 0, tokens_out: int = 0, cost: float = 0.0) -> None:
    span = get_current_span()
    if span is None:
        return

    try:
        span.tokens_in += tokens_in
        span.tokens_out += tokens_out
        span.cost += cost
    except Exception:
        return

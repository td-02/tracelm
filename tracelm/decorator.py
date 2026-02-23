from __future__ import annotations

from functools import wraps
from inspect import iscoroutinefunction
from typing import Any, Callable, Dict, Optional, TypeVar, cast

from tracelm.context import (
    generate_span_id,
    get_current_span,
    get_current_trace,
    is_tracing_enabled,
    set_current_span,
)
from tracelm.span import Span
from tracelm.trace import Trace

F = TypeVar("F", bound=Callable[..., Any])

_TRACE_REGISTRY: Dict[str, Trace] = {}


def get_trace(trace_id: str) -> Optional[Trace]:
    return _TRACE_REGISTRY.get(trace_id)


def _get_active_trace() -> Trace:
    current_trace = get_current_trace()

    if isinstance(current_trace, Trace):
        _TRACE_REGISTRY[current_trace.trace_id] = current_trace
        return current_trace

    if isinstance(current_trace, str):
        existing = _TRACE_REGISTRY.get(current_trace)
        if existing is not None:
            return existing
        new_trace = Trace(trace_id=current_trace)
        _TRACE_REGISTRY[current_trace] = new_trace
        return new_trace

    raise RuntimeError("No active trace. Use CLI run command.")


def node(name: str) -> Callable[[F], F]:
    if not name:
        raise ValueError("name must be a non-empty string")

    def decorator(func: F) -> F:
        if iscoroutinefunction(func):

            @wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                if not is_tracing_enabled():
                    return await func(*args, **kwargs)

                trace = _get_active_trace()
                parent_span = get_current_span()
                if not isinstance(parent_span, Span):
                    raise RuntimeError("No active parent span. CLI must initialize root span.")
                parent_id = parent_span.span_id

                span = Span(
                    span_id=generate_span_id(),
                    trace_id=trace.trace_id,
                    parent_id=parent_id,
                    name=name,
                )
                trace.add_span(span)
                set_current_span(span)

                try:
                    return await func(*args, **kwargs)
                except Exception as exc:
                    span.error = f"{type(exc).__name__}: {exc}"
                    raise
                finally:
                    span.finish()
                    set_current_span(parent_span)

            return cast(F, async_wrapper)

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            if not is_tracing_enabled():
                return func(*args, **kwargs)

            trace = _get_active_trace()
            parent_span = get_current_span()
            if not isinstance(parent_span, Span):
                raise RuntimeError("No active parent span. CLI must initialize root span.")
            parent_id = parent_span.span_id

            span = Span(
                span_id=generate_span_id(),
                trace_id=trace.trace_id,
                parent_id=parent_id,
                name=name,
            )
            trace.add_span(span)
            set_current_span(span)

            try:
                return func(*args, **kwargs)
            except Exception as exc:
                span.error = f"{type(exc).__name__}: {exc}"
                raise
            finally:
                span.finish()
                set_current_span(parent_span)

        return cast(F, sync_wrapper)

    return decorator

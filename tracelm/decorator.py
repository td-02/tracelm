from __future__ import annotations

from functools import wraps
from inspect import iscoroutinefunction
from typing import Any, Callable, Dict, Optional, TypeVar, cast
from uuid import uuid4

from tracelm.context import get_current_span, get_current_trace, set_current_span
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
                trace = _get_active_trace()
                parent_span = get_current_span()
                parent_id = parent_span.span_id if isinstance(parent_span, Span) else None

                span = Span(
                    span_id=uuid4().hex,
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
            trace = _get_active_trace()
            parent_span = get_current_span()
            parent_id = parent_span.span_id if isinstance(parent_span, Span) else None

            span = Span(
                span_id=uuid4().hex,
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

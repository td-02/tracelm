from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from tracelm import context as _context
from tracelm import decorator as _decorator
from tracelm.context import create_new_trace, generate_span_id, get_current_trace, set_current_span
from tracelm.decorator import get_trace
from tracelm.distributed.tracecontext import build_traceparent, parse_traceparent
from tracelm.profiler import generate_summary
from tracelm.span import Span
from tracelm.storage.sqlite_store import save_trace
from tracelm.trace import Trace


class TraceLMMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, store_traces: bool = True) -> None:
        super().__init__(app)
        self.store_traces = store_traces

    async def dispatch(self, request: Request, call_next) -> Response:
        incoming_parent_id: str | None = None
        traceparent = request.headers.get("traceparent")

        if traceparent:
            parsed = parse_traceparent(traceparent)
            if parsed is not None:
                incoming_trace_id, incoming_parent_id = parsed
                _context._current_trace.set(incoming_trace_id)
                set_current_span(None)
                trace = get_trace(incoming_trace_id)
                if trace is None:
                    trace = Trace(trace_id=incoming_trace_id)
                    _decorator._TRACE_REGISTRY[incoming_trace_id] = trace
            else:
                create_new_trace()
                trace = None
        else:
            create_new_trace()
            trace = None

        if trace is None:
            trace_ref = get_current_trace()
            if isinstance(trace_ref, Trace):
                trace = trace_ref
            elif isinstance(trace_ref, str):
                trace = get_trace(trace_ref)
                if trace is None:
                    trace = Trace(trace_id=trace_ref)
                    _decorator._TRACE_REGISTRY[trace_ref] = trace
            else:
                raise RuntimeError("No active trace. Use CLI run command.")

        root_span = Span(
            span_id=generate_span_id(),
            trace_id=trace.trace_id,
            parent_id=incoming_parent_id,
            name=f"{request.method} {request.url.path}",
        )
        trace.add_span(root_span)
        set_current_span(root_span)

        try:
            response = await call_next(request)
            root_span.finish()
            response.headers["traceparent"] = build_traceparent(trace.trace_id, root_span.span_id)
            trace.validate()
            _ = generate_summary(trace)
            if self.store_traces:
                save_trace(trace)
            return response
        except Exception:
            root_span.finish()
            raise

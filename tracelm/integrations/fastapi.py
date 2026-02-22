from __future__ import annotations

import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from tracelm import decorator as _decorator
from tracelm.context import create_new_trace, get_current_trace, set_current_span
from tracelm.decorator import get_trace
from tracelm.profiler import generate_summary
from tracelm.span import Span
from tracelm.storage.sqlite_store import save_trace
from tracelm.trace import Trace


class TraceLMMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, store_traces: bool = True) -> None:
        super().__init__(app)
        self.store_traces = store_traces

    async def dispatch(self, request: Request, call_next) -> Response:
        create_new_trace()
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
            span_id=str(uuid.uuid4()),
            trace_id=trace.trace_id,
            parent_id=None,
            name=f"{request.method} {request.url.path}",
        )
        trace.add_span(root_span)
        set_current_span(root_span)

        try:
            response = await call_next(request)
            root_span.finish()
            trace.validate()
            _ = generate_summary(trace)
            if self.store_traces:
                save_trace(trace)
            return response
        except Exception:
            root_span.finish()
            raise

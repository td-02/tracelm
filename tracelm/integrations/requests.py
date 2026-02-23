from __future__ import annotations

from typing import Any, Callable

from tracelm.context import get_current_span, get_current_trace
from tracelm.distributed.tracecontext import build_traceparent

_original_request: Callable[..., Any] | None = None
_is_patched = False


def patch_requests() -> None:
    global _original_request, _is_patched

    if _is_patched:
        return

    import requests

    _original_request = requests.Session.request

    def wrapper(self: requests.Session, method: str, url: str, **kwargs: Any) -> Any:
        trace = get_current_trace()
        span = get_current_span()

        trace_id: str | None = None
        if isinstance(trace, str):
            trace_id = trace
        elif trace is not None:
            trace_id = getattr(trace, "trace_id", None)

        span_id = getattr(span, "span_id", None)

        if trace_id and span_id:
            headers = kwargs.get("headers")
            if headers is None:
                headers = {}
                kwargs["headers"] = headers

            if "traceparent" not in headers:
                headers["traceparent"] = build_traceparent(trace_id, span_id)

        return _original_request(self, method, url, **kwargs)

    requests.Session.request = wrapper
    _is_patched = True

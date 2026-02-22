from __future__ import annotations

from typing import Any

from tracelm.span import Span
from tracelm.trace import Trace

_tracer: Any | None = None


def enable_otel_bridge(service_name: str = "tracelm") -> None:
    global _tracer

    try:
        from opentelemetry import trace
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor
    except ImportError as exc:
        raise ImportError(
            "OpenTelemetry bridge requires optional dependency 'opentelemetry-sdk'. "
            "Install with: pip install opentelemetry-sdk"
        ) from exc

    resource = Resource.create({"service.name": service_name})
    provider = TracerProvider(resource=resource)
    processor = SimpleSpanProcessor(ConsoleSpanExporter())
    provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)
    _tracer = trace.get_tracer("tracelm")


def create_otel_span(span: Span) -> None:
    if _tracer is None:
        raise RuntimeError("OpenTelemetry bridge is not enabled. Call enable_otel_bridge() first.")

    with _tracer.start_as_current_span(span.name) as otel_span:
        otel_span.set_attribute("tokens.in", int(span.tokens_in))
        otel_span.set_attribute("tokens.out", int(span.tokens_out))
        otel_span.set_attribute("cost", float(span.cost))


def export_trace_to_otel_sdk(trace: Trace) -> None:
    for span in trace.spans.values():
        create_otel_span(span)

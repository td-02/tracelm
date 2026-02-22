from __future__ import annotations

import json
from typing import Any

from tracelm.trace import Trace


def _normalize_hex(value: str) -> str:
    return value.replace("-", "")


def export_trace_to_otel(trace: Trace, output_file: str) -> None:
    trace_id = _normalize_hex(trace.trace_id)

    spans: list[dict[str, Any]] = []
    for span in trace.spans.values():
        span_id = _normalize_hex(span.span_id)[:16]
        parent_span_id = ""
        if span.parent_id:
            parent_span_id = _normalize_hex(span.parent_id)[:16]

        spans.append(
            {
                "traceId": trace_id,
                "spanId": span_id,
                "parentSpanId": parent_span_id,
                "name": span.name,
                "startTimeUnixNano": int(float(span.start_time) * 1_000_000_000),
                "endTimeUnixNano": int(float(span.end_time) * 1_000_000_000),
                "attributes": [
                    {"key": "tokens.in", "value": {"intValue": int(span.tokens_in)}},
                    {"key": "tokens.out", "value": {"intValue": int(span.tokens_out)}},
                    {"key": "cost", "value": {"doubleValue": float(span.cost)}},
                ],
            }
        )

    payload = {
        "resourceSpans": [
            {
                "resource": {
                    "attributes": [
                        {"key": "service.name", "value": {"stringValue": "tracelm"}},
                    ]
                },
                "scopeSpans": [
                    {
                        "scope": {"name": "tracelm"},
                        "spans": spans,
                    }
                ],
            }
        ]
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(payload, f)

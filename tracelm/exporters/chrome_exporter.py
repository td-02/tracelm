from __future__ import annotations

import json
from typing import Any

from tracelm.trace import Trace


def export_trace_to_chrome(trace: Trace, output_file: str) -> None:
    root = trace.get_root_span()
    if root is not None:
        baseline = float(root.start_time)
    elif trace.spans:
        baseline = min(float(span.start_time) for span in trace.spans.values())
    else:
        baseline = 0.0

    events: list[dict[str, Any]] = []
    for span in trace.spans.values():
        ts = int((float(span.start_time) - baseline) * 1_000_000)
        dur = int(float(span.duration) * 1_000_000)
        if ts < 0:
            ts = 0
        if dur < 0:
            dur = 0

        events.append(
            {
                "name": span.name,
                "ph": "X",
                "ts": ts,
                "dur": dur,
                "pid": 1,
                "tid": 1,
            }
        )

    payload = {"traceEvents": events}
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(payload, f)

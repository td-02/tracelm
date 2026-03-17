from __future__ import annotations

from typing import Dict, List, Tuple

from tracelm.span import Span
from tracelm.trace import Trace


def compute_total_latency(trace: Trace) -> float:
    root = trace.get_root_span()
    if root is None:
        return 0.0
    return float(root.duration)


def build_duration_histogram(
    trace: Trace,
    bucket_bounds_ms: list[float] | None = None,
) -> list[dict[str, float | int | str | None]]:
    user_spans = [span for span in trace.spans.values() if span.name != "__root__"]
    if not user_spans:
        return []

    bounds = bucket_bounds_ms or [0.1, 0.5, 1.0, 5.0, 10.0, 50.0, 100.0, 500.0, 1000.0]
    histogram: list[dict[str, float | int | str | None]] = []
    lower_bound = 0.0

    for upper_bound in bounds:
        histogram.append(
            {
                "label": f"{lower_bound:.3f}-{upper_bound:.3f}",
                "lower_ms": lower_bound,
                "upper_ms": upper_bound,
                "count": 0,
            }
        )
        lower_bound = upper_bound

    histogram.append(
        {
            "label": f"> {bounds[-1]:.3f}",
            "lower_ms": bounds[-1],
            "upper_ms": None,
            "count": 0,
        }
    )

    for span in user_spans:
        duration_ms = float(span.duration) * 1000.0
        for bucket in histogram:
            upper_ms = bucket["upper_ms"]
            if upper_ms is None:
                bucket["count"] += 1
                break
            if duration_ms <= upper_ms:
                bucket["count"] += 1
                break

    return histogram


def find_slowest_span(trace: Trace) -> Span | None:
    user_spans = [span for span in trace.spans.values() if span.name != "__root__"]
    if not user_spans:
        return None
    return max(user_spans, key=lambda span: span.duration)


def compute_critical_path(trace: Trace) -> list[str]:
    root = trace.get_root_span()
    if root is None:
        return []

    children_by_parent: Dict[str, List[str]] = {span_id: [] for span_id in trace.spans}
    for span in trace.spans.values():
        if span.parent_id is not None and span.parent_id in children_by_parent:
            children_by_parent[span.parent_id].append(span.span_id)

    memo: Dict[str, Tuple[float, List[str]]] = {}

    def dfs(span_id: str) -> Tuple[float, List[str]]:
        cached = memo.get(span_id)
        if cached is not None:
            return cached

        span = trace.get_span(span_id)
        if span is None:
            result = (0.0, [])
            memo[span_id] = result
            return result

        best_child_total = 0.0
        best_child_path: List[str] = []

        for child_id in children_by_parent.get(span_id, []):
            child_total, child_path = dfs(child_id)
            if child_total > best_child_total:
                best_child_total = child_total
                best_child_path = child_path

        total = float(span.duration) + best_child_total
        path = [span.name, *best_child_path]
        result = (total, path)
        memo[span_id] = result
        return result

    return dfs(root.span_id)[1]


def detect_anomalies(trace: Trace) -> dict:
    user_spans = [span for span in trace.spans.values() if span.name != "__root__"]
    if not user_spans:
        return {"latency_spikes": []}

    durations = [span.duration for span in user_spans]
    mean_duration = sum(durations) / len(durations)
    threshold = mean_duration * 2

    spikes = [span.name for span in user_spans if span.duration > threshold]
    return {"latency_spikes": spikes}


def generate_summary(trace: Trace) -> dict:
    slowest = find_slowest_span(trace)
    total_tokens_in = sum(span.tokens_in for span in trace.spans.values())
    total_tokens_out = sum(span.tokens_out for span in trace.spans.values())
    total_cost = sum(span.cost for span in trace.spans.values())

    return {
        "trace_id": trace.trace_id,
        "total_latency": compute_total_latency(trace),
        "total_spans": len(trace.spans),
        "slowest_span": slowest.name if slowest is not None else "",
        "critical_path": compute_critical_path(trace),
        "total_tokens_in": total_tokens_in,
        "total_tokens_out": total_tokens_out,
        "total_cost": total_cost,
        "anomalies": detect_anomalies(trace),
        "duration_histogram_ms": build_duration_histogram(trace),
    }

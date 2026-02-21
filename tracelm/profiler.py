from __future__ import annotations

from typing import Dict, List, Tuple

from tracelm.span import Span
from tracelm.trace import Trace


def compute_total_latency(trace: Trace) -> float:
    root = trace.get_root_span()
    if root is None:
        return 0.0
    return float(root.duration)


def find_slowest_span(trace: Trace) -> Span | None:
    if not trace.spans:
        return None
    return max(trace.spans.values(), key=lambda span: span.duration)


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
    if not trace.spans:
        return {"latency_spikes": []}

    durations = [span.duration for span in trace.spans.values()]
    mean_duration = sum(durations) / len(durations)
    threshold = mean_duration * 2

    spikes = [span.name for span in trace.spans.values() if span.duration > threshold]
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
    }

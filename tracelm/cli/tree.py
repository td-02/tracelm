from __future__ import annotations

import sys
from typing import Dict, List, Optional

from tracelm.span import Span
from tracelm.trace import Trace


def _format_span_line(span: Span) -> str:
    duration_ms = float(span.duration) * 1000.0
    return f"{span.name} ({duration_ms:.3f} ms)"


def _find_entry_span(trace: Trace, children_by_parent: Dict[str, List[str]]) -> Optional[Span]:
    roots = [span for span in trace.spans.values() if span.parent_id is None]
    if len(roots) == 1:
        return roots[0]

    distributed_entries = [
        span for span in trace.spans.values() if span.parent_id is not None and span.parent_id not in trace.spans
    ]
    if len(distributed_entries) == 1:
        return distributed_entries[0]

    if trace.spans:
        return min(trace.spans.values(), key=lambda s: s.start_time)

    return None


def render_trace_tree(trace: Trace) -> str:
    if not trace.spans:
        return ""

    encoding = sys.stdout.encoding
    if encoding is None or "utf" not in encoding.lower():
        branch = "+-- "
        last_branch = "\\-- "
        vertical = "|   "
    else:
        branch = "\u251c\u2500\u2500 "
        last_branch = "\u2514\u2500\u2500 "
        vertical = "\u2502   "

    space = "    "

    children_by_parent: Dict[str, List[str]] = {span_id: [] for span_id in trace.spans}
    for span in trace.spans.values():
        if span.parent_id is not None and span.parent_id in trace.spans:
            children_by_parent[span.parent_id].append(span.span_id)

    for parent_id, child_ids in children_by_parent.items():
        child_ids.sort(key=lambda child_id: trace.spans[child_id].start_time)

    entry = _find_entry_span(trace, children_by_parent)
    if entry is None:
        return ""

    lines: List[str] = [_format_span_line(entry)]

    def walk(span_id: str, prefix: str) -> None:
        child_ids = children_by_parent.get(span_id, [])
        for index, child_id in enumerate(child_ids):
            child = trace.spans[child_id]
            is_last = index == len(child_ids) - 1
            connector = last_branch if is_last else branch
            lines.append(f"{prefix}{connector}{_format_span_line(child)}")
            next_prefix = prefix + (space if is_last else vertical)
            walk(child_id, next_prefix)

    walk(entry.span_id, "")
    return "\n".join(lines)

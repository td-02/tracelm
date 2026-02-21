from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional, Set

from tracelm.span import Span


@dataclass(slots=True)
class Trace:
    trace_id: str
    spans: Dict[str, Span] = field(default_factory=dict)
    root_span_id: Optional[str] = None

    def add_span(self, span: Span) -> None:
        if span.trace_id != self.trace_id:
            raise ValueError("span.trace_id must match trace.trace_id")

        self.spans[span.span_id] = span

        if span.parent_id is None:
            self.root_span_id = span.span_id
        else:
            parent = self.spans.get(span.parent_id)
            if parent is not None and span.span_id not in parent.children:
                parent.children.append(span.span_id)

        for candidate in self.spans.values():
            if candidate.parent_id == span.span_id and candidate.span_id not in span.children:
                span.children.append(candidate.span_id)

    def get_root_span(self) -> Optional[Span]:
        if self.root_span_id is None:
            return None
        return self.spans.get(self.root_span_id)

    def get_span(self, span_id: str) -> Optional[Span]:
        return self.spans.get(span_id)

    def validate(self) -> None:
        roots = [span for span in self.spans.values() if span.parent_id is None]
        if len(roots) != 1:
            raise ValueError("trace must contain exactly one root span")

        root = roots[0]
        visited: Set[str] = set()
        stack = [root.span_id]

        children_by_parent: Dict[str, Set[str]] = {span_id: set() for span_id in self.spans}
        for span in self.spans.values():
            if span.parent_id is None:
                continue
            if span.parent_id not in self.spans:
                raise ValueError(f"parent span '{span.parent_id}' not found for span '{span.span_id}'")
            children_by_parent[span.parent_id].add(span.span_id)

        while stack:
            current = stack.pop()
            if current in visited:
                continue
            visited.add(current)
            stack.extend(children_by_parent.get(current, set()) - visited)

        if len(visited) != len(self.spans):
            raise ValueError("all spans must be reachable from the root span")

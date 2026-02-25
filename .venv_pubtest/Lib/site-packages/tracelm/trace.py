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
        external_parents = [
            span for span in self.spans.values() if span.parent_id is not None and span.parent_id not in self.spans
        ]

        is_local = len(roots) == 1 and len(external_parents) == 0
        is_distributed = len(roots) == 0 and len(external_parents) == 1
        if not (is_local or is_distributed):
            raise ValueError("invalid trace structure")

        entry_span = roots[0] if is_local else external_parents[0]

        children_by_parent: Dict[str, Set[str]] = {span_id: set() for span_id in self.spans}
        for span in self.spans.values():
            if span.parent_id is None or span.parent_id not in self.spans:
                continue
            children_by_parent[span.parent_id].add(span.span_id)

        state: Dict[str, int] = {span_id: 0 for span_id in self.spans}
        visited: Set[str] = set()

        def dfs(span_id: str) -> None:
            status = state[span_id]
            if status == 1:
                raise ValueError("invalid trace structure")
            if status == 2:
                return

            state[span_id] = 1
            visited.add(span_id)
            for child_id in children_by_parent.get(span_id, set()):
                dfs(child_id)
            state[span_id] = 2

        dfs(entry_span.span_id)

        if len(visited) != len(self.spans):
            raise ValueError("invalid trace structure")

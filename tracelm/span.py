from __future__ import annotations

from dataclasses import dataclass, field
from time import perf_counter
from typing import Any, Dict, List, Optional

from tracelm.context import generate_span_id


def _is_lower_hex(value: str, length: int) -> bool:
    if len(value) != length:
        return False
    allowed = set("0123456789abcdef")
    return all(ch in allowed for ch in value)


@dataclass(slots=True)
class Span:
    trace_id: str
    name: str
    span_id: str = field(default_factory=generate_span_id)
    parent_id: Optional[str] = None
    start_time: float = field(default_factory=perf_counter)
    end_time: float = 0.0
    duration: float = 0.0
    tokens_in: int = 0
    tokens_out: int = 0
    cost: float = 0.0
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    children: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.span_id = self.span_id.lower()
        self.trace_id = self.trace_id.lower()
        if self.parent_id is not None:
            self.parent_id = self.parent_id.lower()

        if not self.span_id:
            raise ValueError("span_id must be a non-empty string")
        if not _is_lower_hex(self.span_id, 16) or self.span_id == "0" * 16:
            raise ValueError("span_id must be 16 lowercase hex characters and not all zeros")

        if not self.trace_id:
            raise ValueError("trace_id must be a non-empty string")
        if not _is_lower_hex(self.trace_id, 32) or self.trace_id == "0" * 32:
            raise ValueError("trace_id must be 32 lowercase hex characters and not all zeros")

        if self.parent_id is not None:
            if not _is_lower_hex(self.parent_id, 16) or self.parent_id == "0" * 16:
                raise ValueError("parent_id must be 16 lowercase hex characters and not all zeros")

        if not self.name:
            raise ValueError("name must be a non-empty string")
        if self.tokens_in < 0:
            raise ValueError("tokens_in must be >= 0")
        if self.tokens_out < 0:
            raise ValueError("tokens_out must be >= 0")
        if self.cost < 0:
            raise ValueError("cost must be >= 0")

    def finish(self) -> None:
        end = perf_counter()
        if end < self.start_time:
            end = self.start_time
        self.end_time = end
        self.duration = self.end_time - self.start_time

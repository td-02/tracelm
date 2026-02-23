from __future__ import annotations


def _is_hex(value: str) -> bool:
    if not value:
        return False
    return all(ch in "0123456789abcdefABCDEF" for ch in value)


def parse_traceparent(header: str) -> tuple[str, str] | None:
    parts = header.split("-")
    if len(parts) != 4:
        return None

    _, trace_id, span_id, _ = parts

    if len(trace_id) != 32:
        return None
    if len(span_id) != 16:
        return None
    if not _is_hex(trace_id) or not _is_hex(span_id):
        return None

    return trace_id.lower(), span_id.lower()


def build_traceparent(trace_id: str, span_id: str) -> str:
    return f"00-{trace_id}-{span_id}-01"

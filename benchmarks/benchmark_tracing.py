from __future__ import annotations

from time import perf_counter

from tracelm.context import create_new_trace, set_current_span
from tracelm.decorator import node
from tracelm.span import Span
from tracelm.trace import Trace

ITERATIONS = 100_000


def plain_compute(x: int) -> int:
    return x + 1


@node("bench.compute")
def traced_compute(x: int) -> int:
    return x + 1


def _init_trace_context() -> None:
    trace_id = create_new_trace()
    trace = Trace(trace_id=trace_id)

    from tracelm import decorator as _decorator

    _decorator._TRACE_REGISTRY[trace_id] = trace

    root = Span(span_id="benchmark_root", trace_id=trace_id, parent_id=None, name="__root__")
    trace.add_span(root)
    set_current_span(root)


def _run_plain() -> float:
    start = perf_counter()
    acc = 0
    for i in range(ITERATIONS):
        acc += plain_compute(i)
    end = perf_counter()
    if acc == -1:
        raise RuntimeError("unreachable")
    return end - start


def _run_traced() -> float:
    _init_trace_context()
    start = perf_counter()
    acc = 0
    for i in range(ITERATIONS):
        acc += traced_compute(i)
    end = perf_counter()
    if acc == -1:
        raise RuntimeError("unreachable")
    return end - start


def main() -> None:
    baseline = _run_plain()
    traced = _run_traced()
    overhead = ((traced - baseline) / baseline * 100.0) if baseline > 0 else 0.0

    print(f"Baseline time: {baseline:.6f}s")
    print(f"Traced time: {traced:.6f}s")
    print(f"Overhead percentage: {overhead:.2f}%")


if __name__ == "__main__":
    main()

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

from tracelm.cli.tree import render_trace_tree
from tracelm.context import create_new_trace, generate_span_id, get_current_span, get_current_trace, record_tokens, set_current_span
from tracelm.decorator import get_trace
from tracelm.exporters.chrome_exporter import export_trace_to_chrome
from tracelm.exporters.otel_exporter import export_trace_to_otel
from tracelm.profiler import generate_summary
from tracelm.sampling import should_sample
from tracelm.span import Span
from tracelm.storage.sqlite_store import init_db, latest_trace_id, list_traces, load_trace, save_trace
from tracelm.trace import Trace

INIT_TEMPLATE = """from tracelm.decorator import node


@node("load_data")
def load_data() -> list[int]:
    return [1, 2, 3]


@node("compute_total")
def compute_total(values: list[int]) -> int:
    return sum(values)


def main() -> int:
    values = load_data()
    total = compute_total(values)
    print({"total": total})
    return total


if __name__ == "__main__":
    main()
"""


def _resolve_trace_object() -> Trace | None:
    current = get_current_trace()
    if isinstance(current, Trace):
        return current
    if isinstance(current, str):
        return get_trace(current)
    return None


def _trace_from_data(data: dict[str, Any]) -> Trace:
    trace = Trace(trace_id=str(data.get("trace_id", "")))
    spans_data = data.get("spans", {})

    if isinstance(spans_data, dict):
        for span_id, span_payload in spans_data.items():
            if not isinstance(span_payload, dict):
                continue
            payload = dict(span_payload)
            payload.setdefault("span_id", span_id)
            payload.setdefault("trace_id", trace.trace_id)
            payload.setdefault("name", str(payload.get("span_id", span_id)))
            span = Span(**payload)
            trace.spans[span.span_id] = span

    root_span_id = data.get("root_span_id")
    trace.root_span_id = root_span_id if isinstance(root_span_id, str) else None
    return trace


def _print_summary(summary: dict[str, Any]) -> None:
    critical_path = " -> ".join(summary["critical_path"])

    print("Trace Summary")
    print("-------------")
    print(f"Trace ID: {summary['trace_id']}")
    print(f"Total Latency: {summary['total_latency']}")
    print(f"Total Spans: {summary['total_spans']}")
    print(f"Slowest Span: {summary['slowest_span']}")
    print(f"Critical Path: {critical_path}")
    print(f"Tokens In: {summary['total_tokens_in']}")
    print(f"Tokens Out: {summary['total_tokens_out']}")
    print(f"Total Cost: {summary['total_cost']}")
    print(f"Anomalies: {summary['anomalies']}")

    histogram = summary.get("duration_histogram_ms", [])
    if histogram:
        print("")
        print("Duration Histogram (ms)")
        print("-----------------------")
        for bucket in histogram:
            print(f"{bucket['label']}: {bucket['count']}")


def _resolve_user_trace_id(trace_id: str) -> str | None:
    if trace_id != "latest":
        return trace_id
    return latest_trace_id()


def _print_missing_trace(message: str) -> None:
    print(message)


def _render_trace(trace: Trace) -> None:
    summary = generate_summary(trace)
    print("")
    _print_summary(summary)
    print("")
    print("Execution Tree")
    print("--------------")
    print(render_trace_tree(trace))


def _finalize_trace(trace: Trace, otel: bool = False) -> None:
    trace.validate()
    if otel:
        from tracelm.bridges.otel_bridge import enable_otel_bridge, export_trace_to_otel_sdk

        enable_otel_bridge()
        export_trace_to_otel_sdk(trace)
    save_trace(trace)
    _render_trace(trace)


def _cmd_run(python_file: str, otel: bool = False, sample_rate: float = 1.0) -> None:
    source = Path(python_file).read_text(encoding="utf-8")
    execution_globals = {"__name__": "__main__", "__file__": str(Path(python_file).resolve())}

    if not should_sample(sample_rate):
        from tracelm.context import set_tracing_enabled

        set_tracing_enabled(False)
        exec(source, execution_globals)
        return

    create_new_trace()

    from tracelm import decorator as _decorator

    trace_ref = get_current_trace()
    if isinstance(trace_ref, Trace):
        trace = trace_ref
    elif isinstance(trace_ref, str):
        trace = get_trace(trace_ref)
        if trace is None:
            trace = Trace(trace_id=trace_ref)
            _decorator._TRACE_REGISTRY[trace_ref] = trace
    else:
        raise RuntimeError("No active trace. Use CLI run command.")

    root_span = Span(
        span_id=generate_span_id(),
        trace_id=trace.trace_id,
        parent_id=None,
        name="__root__",
    )

    trace.add_span(root_span)
    set_current_span(root_span)

    exec(source, execution_globals)

    from tracelm.context import get_current_span

    current_span = get_current_span()
    if current_span is not None:
        current_span.finish()

    trace = _resolve_trace_object()
    if trace is not None:
        _finalize_trace(trace, otel=otel)


def _cmd_demo(otel: bool = False, sample_rate: float = 1.0) -> None:
    from tracelm.decorator import node

    @node("load_prompt")
    def load_prompt() -> str:
        time.sleep(0.001)
        record_tokens(tokens_in=24)
        return "Summarize the customer ticket."

    @node("retrieve_context")
    def retrieve_context(_: str) -> str:
        time.sleep(0.002)
        return "Billing issue context"

    @node("llm_call")
    def llm_call(prompt: str, context: str) -> str:
        time.sleep(0.003)
        record_tokens(tokens_in=len(prompt.split()) + len(context.split()), tokens_out=42, cost=0.0008)
        return "Summary ready"

    @node("format_response")
    def format_response(result: str) -> dict[str, str]:
        time.sleep(0.001)
        return {"result": result}

    if not should_sample(sample_rate):
        print("Sampling skipped tracing for this demo run.")
        return

    create_new_trace()
    trace_ref = get_current_trace()
    if not isinstance(trace_ref, str):
        raise RuntimeError("No active trace. Use CLI run command.")

    from tracelm import decorator as _decorator

    trace = get_trace(trace_ref)
    if trace is None:
        trace = Trace(trace_id=trace_ref)
        _decorator._TRACE_REGISTRY[trace_ref] = trace

    root_span = Span(
        span_id=generate_span_id(),
        trace_id=trace.trace_id,
        parent_id=None,
        name="__root__",
    )
    trace.add_span(root_span)
    set_current_span(root_span)

    prompt = load_prompt()
    context = retrieve_context(prompt)
    result = llm_call(prompt, context)
    format_response(result)

    current_span = get_current_span()
    if current_span is not None:
        current_span.finish()

    resolved_trace = _resolve_trace_object()
    if resolved_trace is not None:
        _finalize_trace(resolved_trace, otel=otel)


def _cmd_analyze(trace_id: str, as_json: bool = False) -> None:
    resolved_trace_id = _resolve_user_trace_id(trace_id)
    if resolved_trace_id is None:
        if as_json:
            print("null")
            return
        _print_missing_trace("No stored traces found. Run `tracelm demo` or `tracelm run <file>` first.")
        return

    data = load_trace(resolved_trace_id)
    if data is None:
        if as_json:
            print("null")
            return
        _print_missing_trace(f"Trace '{trace_id}' was not found.")
        return
    if as_json:
        print(json.dumps(data))
        return

    trace = _trace_from_data(data)
    summary = generate_summary(trace)
    _print_summary(summary)
    print("")
    print("Execution Tree")
    print("--------------")
    print(render_trace_tree(trace))


def _cmd_export(trace_id: str, export_format: str) -> None:
    resolved_trace_id = _resolve_user_trace_id(trace_id)
    if resolved_trace_id is None:
        _print_missing_trace("No stored traces found. Run `tracelm demo` or `tracelm run <file>` first.")
        return

    data = load_trace(resolved_trace_id)
    if data is None:
        _print_missing_trace(f"Trace '{trace_id}' was not found.")
        return

    trace = _trace_from_data(data)

    if export_format == "chrome":
        output_file = f"trace_{resolved_trace_id}.json"
        export_trace_to_chrome(trace, output_file)
        print(f"Exported to {output_file}")
        return

    if export_format == "otel":
        output_file = f"trace_{resolved_trace_id}_otel.json"
        export_trace_to_otel(trace, output_file)
        print(f"Exported to {output_file}")


def _cmd_compare(trace_id_1: str, trace_id_2: str) -> None:
    resolved_trace_id_1 = _resolve_user_trace_id(trace_id_1)
    resolved_trace_id_2 = _resolve_user_trace_id(trace_id_2)

    if resolved_trace_id_1 is None or resolved_trace_id_2 is None:
        _print_missing_trace("Not enough stored traces found to compare.")
        return

    data_1 = load_trace(resolved_trace_id_1)
    data_2 = load_trace(resolved_trace_id_2)

    if data_1 is None or data_2 is None:
        _print_missing_trace("One or both traces could not be found for comparison.")
        return

    trace_1 = _trace_from_data(data_1)
    trace_2 = _trace_from_data(data_2)

    summary_1 = generate_summary(trace_1)
    summary_2 = generate_summary(trace_2)

    latency_1 = summary_1["total_latency"]
    latency_2 = summary_2["total_latency"]
    cost_1 = summary_1["total_cost"]
    cost_2 = summary_2["total_cost"]
    tokens_out_1 = summary_1["total_tokens_out"]
    tokens_out_2 = summary_2["total_tokens_out"]

    print("Trace Comparison")
    print("----------------")
    print(f"Latency 1: {latency_1}")
    print(f"Latency 2: {latency_2}")
    print(f"Latency Delta: {latency_2 - latency_1}")
    print("")
    print(f"Cost 1: {cost_1}")
    print(f"Cost 2: {cost_2}")
    print(f"Cost Delta: {cost_2 - cost_1}")
    print("")
    print(f"Token Delta (out): {tokens_out_2 - tokens_out_1}")


def _cmd_list() -> None:
    for trace_id in list_traces():
        print(trace_id)


def _cmd_latest(as_json: bool = False) -> None:
    _cmd_analyze("latest", as_json=as_json)


def _cmd_init(output_path: str = "tracelm_example.py", force: bool = False) -> None:
    path = Path(output_path)
    if path.exists() and path.is_dir():
        raise IsADirectoryError(f"{path} is a directory. Choose a Python file path instead.")
    if path.exists() and not force:
        raise FileExistsError(f"{path} already exists. Use --force to overwrite it.")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(INIT_TEMPLATE, encoding="utf-8")
    print(f"Created {path}")
    print(f"Next: tracelm run {path}")


def run(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="tracelm",
        description="TraceLM helps you run, inspect, and export Python execution traces.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Run a Python file under tracing.")
    run_parser.add_argument("python_file", help="Path to the Python file to execute.")
    run_parser.add_argument("--otel", action="store_true")
    run_parser.add_argument("--sample-rate", type=float, default=1.0)

    demo_parser = subparsers.add_parser("demo", help="Run a built-in demo trace with no setup.")
    demo_parser.add_argument("--otel", action="store_true")
    demo_parser.add_argument("--sample-rate", type=float, default=1.0)

    init_parser = subparsers.add_parser("init", help="Create a small runnable TraceLM example file.")
    init_parser.add_argument("output", nargs="?", default="tracelm_example.py", help="Output Python file path.")
    init_parser.add_argument("--force", action="store_true", help="Overwrite the output file if it already exists.")

    analyze_parser = subparsers.add_parser("analyze", help="Analyze a stored trace or use 'latest'.")
    analyze_parser.add_argument("trace_id", help="Trace ID to analyze, or 'latest'.")
    analyze_parser.add_argument("--json", action="store_true")

    export_parser = subparsers.add_parser("export", help="Export a stored trace or use 'latest'.")
    export_parser.add_argument("trace_id", help="Trace ID to export, or 'latest'.")
    export_parser.add_argument("--format", dest="export_format", choices=["chrome", "otel"], required=True)

    compare_parser = subparsers.add_parser("compare", help="Compare two traces.")
    compare_parser.add_argument("trace_id_1")
    compare_parser.add_argument("trace_id_2")

    latest_parser = subparsers.add_parser("latest", help="Analyze the most recent stored trace.")
    latest_parser.add_argument("--json", action="store_true")

    subparsers.add_parser("list", help="List stored trace IDs, newest first.")

    args = parser.parse_args(argv)
    init_db()

    if args.command == "run":
        _cmd_run(args.python_file, otel=args.otel, sample_rate=args.sample_rate)
        return
    if args.command == "demo":
        _cmd_demo(otel=args.otel, sample_rate=args.sample_rate)
        return
    if args.command == "init":
        _cmd_init(args.output, force=args.force)
        return
    if args.command == "analyze":
        _cmd_analyze(args.trace_id, as_json=args.json)
        return
    if args.command == "export":
        _cmd_export(args.trace_id, args.export_format)
        return
    if args.command == "compare":
        _cmd_compare(args.trace_id_1, args.trace_id_2)
        return
    if args.command == "latest":
        _cmd_latest(as_json=args.json)
        return
    if args.command == "list":
        _cmd_list()


if __name__ == "__main__":
    run()

from __future__ import annotations

import argparse
import json
import uuid
from pathlib import Path
from typing import Any

from tracelm.cli.tree import render_trace_tree
from tracelm.context import create_new_trace, get_current_trace, set_current_span
from tracelm.decorator import get_trace
from tracelm.exporters.chrome_exporter import export_trace_to_chrome
from tracelm.exporters.otel_exporter import export_trace_to_otel
from tracelm.profiler import generate_summary
from tracelm.span import Span
from tracelm.storage.sqlite_store import init_db, list_traces, load_trace, save_trace
from tracelm.trace import Trace


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


def _cmd_run(python_file: str, otel: bool = False) -> None:
    source = Path(python_file).read_text(encoding="utf-8")
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
        span_id=str(uuid.uuid4()),
        trace_id=trace.trace_id,
        parent_id=None,
        name="__root__",
    )

    trace.add_span(root_span)
    set_current_span(root_span)

    exec(source, {})

    from tracelm.context import get_current_span

    current_span = get_current_span()
    if current_span is not None:
        current_span.finish()

    trace = _resolve_trace_object()
    if trace is not None:
        trace.validate()
        if otel:
            from tracelm.bridges.otel_bridge import enable_otel_bridge, export_trace_to_otel_sdk

            enable_otel_bridge()
            export_trace_to_otel_sdk(trace)
        save_trace(trace)
        summary = generate_summary(trace)
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
        print("")
        print("Execution Tree")
        print("--------------")
        print(render_trace_tree(trace))


def _cmd_analyze(trace_id: str) -> None:
    data = load_trace(trace_id)
    if data is None:
        print("null")
        return
    print(json.dumps(data))


def _cmd_export(trace_id: str, export_format: str) -> None:
    data = load_trace(trace_id)
    if data is None:
        print("null")
        return

    trace = _trace_from_data(data)

    if export_format == "chrome":
        output_file = f"trace_{trace_id}.json"
        export_trace_to_chrome(trace, output_file)
        print(f"Exported to {output_file}")
        return

    if export_format == "otel":
        output_file = f"trace_{trace_id}_otel.json"
        export_trace_to_otel(trace, output_file)
        print(f"Exported to {output_file}")


def _cmd_compare(trace_id_1: str, trace_id_2: str) -> None:
    data_1 = load_trace(trace_id_1)
    data_2 = load_trace(trace_id_2)

    if data_1 is None or data_2 is None:
        print("null")
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


def run(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="tracelm")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("python_file")
    run_parser.add_argument("--otel", action="store_true")

    analyze_parser = subparsers.add_parser("analyze")
    analyze_parser.add_argument("trace_id")

    export_parser = subparsers.add_parser("export")
    export_parser.add_argument("trace_id")
    export_parser.add_argument("--format", dest="export_format", choices=["chrome", "otel"], required=True)

    compare_parser = subparsers.add_parser("compare")
    compare_parser.add_argument("trace_id_1")
    compare_parser.add_argument("trace_id_2")

    subparsers.add_parser("list")

    args = parser.parse_args(argv)
    init_db()

    if args.command == "run":
        _cmd_run(args.python_file, otel=args.otel)
        return
    if args.command == "analyze":
        _cmd_analyze(args.trace_id)
        return
    if args.command == "export":
        _cmd_export(args.trace_id, args.export_format)
        return
    if args.command == "compare":
        _cmd_compare(args.trace_id_1, args.trace_id_2)
        return
    if args.command == "list":
        _cmd_list()


if __name__ == "__main__":
    run()

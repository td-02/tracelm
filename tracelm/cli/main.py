from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from tracelm.context import get_current_trace
from tracelm.decorator import get_trace
from tracelm.storage.sqlite_store import init_db, list_traces, load_trace, save_trace
from tracelm.trace import Trace


def _resolve_trace_object() -> Trace | None:
    current = get_current_trace()
    if isinstance(current, Trace):
        return current
    if isinstance(current, str):
        return get_trace(current)
    return None


def _cmd_run(python_file: str) -> None:
    source = Path(python_file).read_text(encoding="utf-8")
    exec(source, {})

    trace = _resolve_trace_object()
    if trace is not None:
        save_trace(trace)
        print(trace.trace_id)


def _cmd_analyze(trace_id: str) -> None:
    data = load_trace(trace_id)
    if data is None:
        print("null")
        return
    print(json.dumps(data))


def _cmd_list() -> None:
    for trace_id in list_traces():
        print(trace_id)


def run(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="tracelm")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("python_file")

    analyze_parser = subparsers.add_parser("analyze")
    analyze_parser.add_argument("trace_id")

    subparsers.add_parser("list")

    args = parser.parse_args(argv)
    init_db()

    if args.command == "run":
        _cmd_run(args.python_file)
        return
    if args.command == "analyze":
        _cmd_analyze(args.trace_id)
        return
    if args.command == "list":
        _cmd_list()


if __name__ == "__main__":
    run()

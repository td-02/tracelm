# TraceLM
## Open Source LLM Execution Profiler

## Project Overview
TraceLM is a lightweight Python tracing framework for profiling execution flows in LLM-driven applications. It captures span-level timing and hierarchy, propagates context across function boundaries, and provides a simple local persistence and CLI workflow for trace inspection.

## Problem Statement
LLM applications are typically composed of chained function calls, retrieval steps, model invocations, and post-processing logic. Without structured tracing, it is difficult to answer core engineering questions:

- Which step is the latency bottleneck?
- How does execution flow across nested calls?
- Where do failures occur in the pipeline?
- How do token and cost metrics accumulate across components?

TraceLM addresses this by recording execution as structured traces and spans, enabling reproducible profiling and post-run analysis.

## Features (v0.1)
- Context propagation with `contextvars`
- Span model with high-resolution timing (`time.perf_counter`)
- Trace container with parent-child span relationships
- `@node(name)` decorator for sync and async functions
- Automatic trace creation when none exists
- SQLite-backed trace storage (`tracelm_traces.db`)
- CLI commands for run, analyze, and list operations
- Minimal dependency footprint (standard library only)

## Installation

```bash
git clone https://github.com/td-02/tracelm.git
cd tracelm
pip install -e .
```

Alternative (without installation as console script):

```bash
python -m tracelm.cli.main --help
```

## Usage Example

```python
from tracelm.decorator import node


@node("step1")
def step1() -> int:
    return 1


@node("step2")
def step2(x: int) -> int:
    return x + 1


def main() -> int:
    return step2(step1())


main()
```

Run with CLI:

```bash
python -m tracelm.cli.main run test_app.py
```

## CLI Commands

```bash
python -m tracelm.cli.main run <python_file>
python -m tracelm.cli.main analyze <trace_id>
python -m tracelm.cli.main list
```

- `run`: Executes a Python file and persists trace output if generated
- `analyze`: Loads and prints raw JSON trace data for a given trace ID
- `list`: Lists stored trace IDs in reverse chronological order

## Architecture Overview
TraceLM v0.1 consists of four core layers:

- Context layer: `tracelm/context.py` manages active trace/span state via `contextvars`
- Data model layer: `tracelm/span.py` and `tracelm/trace.py` define profiling primitives and graph validation
- Instrumentation layer: `tracelm/decorator.py` creates spans around function execution and links hierarchy
- Persistence/CLI layer: `tracelm/storage/sqlite_store.py` and `tracelm/cli/main.py` provide storage and operational tooling

## Roadmap
- Stable trace lifecycle API (explicit trace start/stop)
- Native token/cost adapters for major LLM providers
- Structured query and filtering for stored traces
- Export formats (JSONL, OpenTelemetry-compatible adapters)
- Visualization utilities for span timelines and call trees
- Test suite expansion and CI integration

## License
MIT License.

## Author
Tapesh  
GitHub: https://github.com/td-02

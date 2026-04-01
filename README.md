# TraceLM

TraceLM is a lightweight execution tracer and profiler for LLM pipelines, RAG systems, and FastAPI-based AI services.

It focuses on the tracing primitives that matter when you want to understand execution flow clearly: span trees, `traceparent` propagation, sampling, profiling, and local inspection.

## Why TraceLM

TraceLM exists for developers who want observability without pulling in a full telemetry stack on day one.

- Trace multi-step LLM workflows with explicit spans
- Validate trace structure before profiling
- Continue traces across service boundaries with W3C `traceparent`
- Inspect latency, critical path, token usage, and cost from the CLI
- Export traces to Chrome Trace or OpenTelemetry-compatible JSON

It is intentionally small, local-first, and easy to read.

## Installation

```bash
pip install tracelm
```

Optional integrations:

```bash
pip install "tracelm[fastapi]"
pip install "tracelm[requests]"
pip install "tracelm[otel]"
```

## Quick Start

Create a small instrumented script:

```python
from tracelm.decorator import node


@node("step1")
def step1() -> int:
    return 1


@node("step2")
def step2(x: int) -> int:
    return x + 1


def main() -> int:
    x = step1()
    return step2(x)


main()
```

Run it:

```bash
tracelm run test_app.py
```

Typical output:

```text
Trace Summary
-------------
Trace ID: 55df12035a754aa080875618bc5794c3
Total Latency: 0.204
Total Spans: 3
Slowest Span: step2
Critical Path: __root__ -> step2
Tokens In: 0
Tokens Out: 0
Total Cost: 0
Anomalies: {'latency_spikes': ['step2']}

Duration Histogram (ms)
-----------------------
0.000-0.100: 1
0.100-0.500: 1
...

Execution Tree
--------------
__root__ (0.204 ms)
+-- step1 (0.082 ms)
\-- step2 (0.101 ms)
```

## Features

- Hierarchical span tracing with a synthetic root span model
- W3C `traceparent` parsing and continuation
- FastAPI middleware integration
- Requests-based outbound propagation
- Head-based probabilistic sampling
- Critical path and slowest-span analysis
- Duration histogram generation
- Token and cost aggregation
- Trace comparison from the CLI
- Chrome Trace export
- OpenTelemetry JSON export and SDK bridge
- SQLite-backed local trace storage

## FastAPI Integration

```python
from fastapi import FastAPI
from tracelm.integrations.fastapi import TraceLMMiddleware

app = FastAPI()
app.add_middleware(TraceLMMiddleware, sample_rate=1.0)


@app.get("/")
def compute():
    return {"status": "ok"}
```

Import the requests integration to propagate trace context on outbound HTTP calls:

```python
import tracelm.integrations.requests
```

## CLI Commands

Run a Python file under tracing:

```bash
tracelm run test_app.py
```

Apply head sampling:

```bash
tracelm run test_app.py --sample-rate 0.1
```

Analyze a stored trace:

```bash
tracelm analyze <trace_id>
```

List stored traces:

```bash
tracelm list
```

Compare two traces:

```bash
tracelm compare <trace_id_1> <trace_id_2>
```

Export to Chrome Trace:

```bash
tracelm export <trace_id> --format chrome
```

Export to OTEL JSON:

```bash
tracelm export <trace_id> --format otel
```

## Design Notes

TraceLM keeps a strict execution model:

- One local root span for CLI-created traces
- Or one continuation entry span when joining an external trace
- DAG validation before profiling
- Async-safe context propagation with `ContextVar`

This keeps behavior predictable and makes failures explicit.

## Scope

TraceLM is currently:

- Single-process
- Developer-focused
- Local-first
- CLI-centered

It is useful for understanding and instrumenting pipelines before adopting heavier observability infrastructure.

## Documentation

- Architecture: `docs/ARCHITECTURE.md`
- Contribution guide: `CONTRIBUTING.md`

## License

MIT

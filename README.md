# TraceLM

Minimal distributed tracing engine built from scratch for understanding and instrumenting LLM pipelines.

TraceLM provides span-level visibility into multi-step LLM workflows, RAG systems, and FastAPI-based AI services. It is intentionally lightweight and dependency-minimal.

---

## Why TraceLM?

I built TraceLM to deeply understand how distributed tracing systems (like OpenTelemetry) actually work internally — including:

- W3C `traceparent` propagation
- Span DAG validation
- Head-based probabilistic sampling
- Async context propagation
- Cross-service continuation
- Execution profiling and critical path detection

It is not meant to replace OpenTelemetry. It is a minimal tracing core designed for clarity, experimentation, and developer-level observability.

---

## Features

- Hierarchical span tracing
- W3C `traceparent` support
- FastAPI middleware integration
- Requests auto-propagation
- Head-based probabilistic sampling
- Critical path detection
- Slowest span identification
- Token and cost aggregation
- Regression comparison between traces
- Chrome Trace export
- OpenTelemetry bridge mode
- CLI tree visualization
- SQLite trace storage

---

## Installation

```bash
pip install tracelm
```

---

## Quick Example

```python
from tracelm.decorator import node

@node("step1")
def step1():
    return 1

@node("step2")
def step2(x):
    return x + 1

def main():
    x = step1()
    return step2(x)

main()
```

Run:

```bash
tracelm run test_app.py
```

Example output:

```
Trace Summary
-------------
Trace ID: 55df12035a754aa080875618bc5794c3
Total Latency: 0.204 ms
Total Spans: 3
Slowest Span: step1

Execution Tree
--------------
__root__ (0.204 ms)
+-- step1 (0.082 ms)
\-- step2 (0.101 ms)
```

---

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

Trace context is propagated via W3C `traceparent` headers.

---

## Distributed Trace Propagation

Outgoing requests can propagate trace context automatically:

```python
import tracelm.integrations.requests
```

Incoming `traceparent` headers are validated and continued correctly.

---

## Sampling

Control tracing overhead:

```bash
tracelm run test_app.py --sample-rate 0.1
```

- `1.0` → trace all executions
- `0.0` → full no-op mode
- Any value between 0 and 1 → probabilistic sampling

Non-sampled executions incur minimal overhead.

---

## Exporting to Chrome Trace

```bash
tracelm export <trace_id> --format chrome
```

Open in:

```
chrome://tracing
```

Load the generated JSON file to inspect execution timelines.

---

## Architecture Overview

Trace lifecycle:

```
CLI run
  → create trace
  → create root span
  → execute user code
  → validate span DAG
  → profile
  → store
  → render summary
```

Distributed continuation allows:

- One local root span
- Or continuation from an external parent trace

Trace invariants are validated before profiling.

---

## Design Goals

- Minimal surface area
- Strict trace invariants
- Async-safe context propagation
- Clear span lifecycle
- No heavy runtime dependencies
- Educational clarity over abstraction

---

## Current Scope

TraceLM is:

- Single-process
- Developer-focused
- Local storage (SQLite)
- CLI-driven

It is intentionally small and transparent.

---

## Roadmap

- Adaptive sampling strategies
- Span duration histograms
- Async task tracing
- HTTP OTEL exporter
- Lightweight web dashboard
- Advanced regression analysis

---

## License

MIT

---

## Author

Tapesh Chandra Das

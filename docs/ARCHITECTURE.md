# TraceLM — Technical Documentation

## 1. Introduction

TraceLM is a minimal distributed tracing engine implemented in Python.  
It is designed to provide execution-level visibility into multi-step LLM workflows, RAG pipelines, and FastAPI-based services.

The system emphasizes:

- Clear span lifecycle management
- Strict trace invariants
- W3C-compliant trace context propagation
- Minimal runtime dependencies
- Educational clarity over abstraction

TraceLM is not intended to replace OpenTelemetry. It is a lightweight tracing core built to understand and instrument distributed execution flows.

---

## 2. Core Concepts

### 2.1 Trace

A trace represents a single logical execution flow.

Properties:
- `trace_id` (32 lowercase hex characters)
- Contains one or more spans
- Forms a directed acyclic graph (DAG)

Trace invariants:
- Exactly one local root span OR
- One span whose parent is external (distributed continuation)
- No cycles
- Every span (except root or continuation entry) must have a valid parent

Validation occurs before profiling.

---

### 2.2 Span

A span represents a timed unit of execution.

Fields:
- `span_id` (16 lowercase hex characters, non-zero)
- `trace_id`
- `parent_id`
- `name`
- `start_time`
- `end_time`
- Optional metadata (tokens, cost, etc.)

Spans are hierarchical.

Example:

```
__root__
 +-- retrieval
 +-- llm_call
```

---

### 2.3 Synthetic Root Model

When using CLI execution mode:

- CLI creates a synthetic root span
- All user spans are children of this root
- The root represents total execution time

This simplifies DAG construction and profiling.

---

### 2.4 Distributed Continuation

TraceLM supports W3C `traceparent` propagation.

Format:
```
traceparent: 00-<trace_id>-<span_id>-01
```

If an inbound request includes a valid header:

- TraceLM continues the existing trace
- No synthetic root is created
- The entry span becomes a continuation node
- DAG validation adapts accordingly

This required modifying the original “exactly one root” invariant.

---

## 3. Execution Lifecycle

### 3.1 CLI Mode

Flow:

```
CLI run
  ? create trace
  ? create root span
  ? execute user code
  ? finish root span
  ? validate DAG
  ? profile
  ? store
  ? render summary
```

CLI owns the trace lifecycle.

Decorators only create spans under the active parent.

---

### 3.2 FastAPI Middleware

When integrated via middleware:

1. Incoming request
2. Check for `traceparent`
3. Decide sampling
4. Create or continue trace
5. Wrap request execution in root span
6. Inject outbound `traceparent` header
7. Validate + store

---

## 4. Context Propagation

TraceLM uses `ContextVar` to maintain active span context.

Advantages:
- Async-safe
- Thread-safe
- No global mutable state leaks
- Minimal overhead

The active span is stored per logical execution context.

Decorators read from the active span context to determine parent-child relationships.

---

## 5. Sampling Model

TraceLM implements head-based probabilistic sampling.

```
should_sample(rate: float)
```

Rules:
- `1.0` ? always sample
- `0.0` ? fully no-op
- `0 < rate < 1` ? random sampling

Non-sampled execution:
- No trace created
- Decorators operate in no-op mode
- No profiling
- Minimal overhead

Sampling is applied at trace creation time.

---

## 6. Profiling Engine

After execution completes:

1. DAG validation
2. Span durations calculated
3. Critical path derived
4. Slowest span identified
5. Token and cost aggregated
6. Anomalies detected (basic latency spike detection)

Summary metrics include:
- Total latency
- Span count
- Critical path
- Slowest span
- Token usage
- Total cost

---

## 7. CLI Commands

Run execution:

```
tracelm run file.py
```

List traces:

```
tracelm list
```

Analyze trace:

```
tracelm analyze <trace_id>
```

Compare traces:

```
tracelm compare <id1> <id2>
```

Export Chrome format:

```
tracelm export <trace_id> --format chrome
```

---

## 8. Storage Layer

TraceLM uses SQLite for local storage.

Stored entities:
- Trace metadata
- Span data
- Profiling results

Design goal:
- Zero external infrastructure
- Deterministic local debugging

---

## 9. OpenTelemetry Bridge

TraceLM includes an optional bridge to the OpenTelemetry SDK.

Purpose:
- Export spans to OTEL collectors
- Integrate with existing observability pipelines

TraceLM maintains its own internal model while optionally forwarding spans.

---

## 10. Design Philosophy

TraceLM prioritizes:

- Minimal core
- Clear invariants
- Explicit lifecycle control
- Educational transparency
- No hidden magic
- No heavy runtime frameworks

Every trace is validated before profiling.

Errors are surfaced explicitly rather than silently ignored.

---

## 11. Limitations

- Single-process execution
- No background worker tracing yet
- No distributed storage backend
- No UI dashboard
- Not production-hardened at scale

---

## 12. Future Directions

- Adaptive sampling strategies
- Span duration histograms
- Async task tracing
- OTEL HTTP exporter
- Web dashboard
- Advanced anomaly detection
- Performance regression thresholds

---

## 13. License

MIT

---

## 14. Author

Tapesh Chandra Das

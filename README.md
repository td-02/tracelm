# TraceLM

## What Is TraceLM
TraceLM is an execution tracer and profiler for LLM systems. It is designed for infrastructure-level visibility into execution flow, latency structure, token usage, and cost signals across traced application nodes.

## Core Features
- Hierarchical span tracing
- Synthetic root span model
- Critical path computation
- Token and cost accounting
- Anomaly detection
- Regression comparison between traces
- Chrome Trace Format export

## Architecture Overview
- CLI owns trace lifecycle by creating the trace context and synthetic root span
- `ContextVar`-based propagation tracks active span state across instrumented calls
- Trace data is represented as a DAG of spans with parent-child relationships
- Profiling and summary generation run after execution completes

## Example CLI Usage
Run:

```bash
python -m tracelm.cli.main run test_app.py
```

Compare:

```bash
python -m tracelm.cli.main compare <id1> <id2>
```

Export:

```bash
python -m tracelm.cli.main export <trace_id> --format chrome
```

## Chrome Trace Visualization
1. Open `chrome://tracing` in Chrome.
2. Load the exported `trace_<trace_id>.json` file.
3. Inspect the timeline view to analyze span durations and nesting.

## Limitations
- Single-process execution model
- No distributed tracing support
- No dedicated UI dashboard

## Roadmap
- Span histograms
- Distributed tracing
- OpenTelemetry compatibility
- Web dashboard

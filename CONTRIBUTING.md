# Contributing to TraceLM

Thank you for contributing to TraceLM.

TraceLM is a minimal distributed tracing engine focused on correctness, clarity, and infrastructure-level observability for multi-step AI systems. Contributions are welcome, but changes must preserve core invariants and design philosophy.

---

## 1. Project Philosophy

TraceLM prioritizes:

- Correct trace invariants
- Minimal surface area
- Clear execution lifecycle
- Async-safe context propagation
- Dependency restraint
- Deterministic behavior

The project favors explicitness over abstraction and correctness over convenience.

---

## 2. Development Setup

Clone the repository:

```bash
git clone https://github.com/td-02/tracelm.git
cd tracelm
```

Create and activate a virtual environment:

```bash
python -m venv venv
# Linux/macOS
source venv/bin/activate
# Windows (PowerShell)
.\venv\Scripts\Activate.ps1
```

Install in editable mode:

```bash
pip install -e .
```

Run tests (if available):

```bash
pytest
```

Run benchmarks:

```bash
python benchmarks/benchmark_tracing.py
```

---

## 3. Project Structure

```
tracelm/
  context.py          # Active trace/span context management
  span.py             # Span model
  trace.py            # Trace model and DAG validation
  profiler.py         # Profiling and critical path logic
  sampling.py         # Head-based sampling logic

  integrations/       # Framework integrations (FastAPI, requests)
  distributed/        # W3C trace context propagation helpers
  exporters/          # Chrome / OTEL export formats
  bridges/            # Runtime bridges (OpenTelemetry SDK)
  storage/            # SQLite storage backend

benchmarks/           # Performance measurement scripts
```

Core engine logic lives under `tracelm/`. Integrations must not weaken trace invariants.

---

## 4. Core Invariants (Must Not Be Broken)

TraceLM enforces:

- A valid DAG (no cycles)
- Exactly one local root OR one distributed continuation entry
- Valid W3C-compliant IDs:
  - 32 lowercase hex trace_id
  - 16 lowercase hex span_id (non-zero)
- Deterministic validation behavior
- Stable parent-child relationships

Any change affecting these must include tests.

---

## 5. Code Guidelines

- Use type hints in all new or modified code.
- Prefer standard library over new dependencies.
- Avoid logging inside core execution paths.
- Keep core engine dependency-free.
- Avoid global mutable state.
- Maintain async safety (ContextVar usage must remain correct).
- Keep changes minimal and well-scoped.

If adding integrations, isolate them under `integrations/`.

---

## 6. Adding a Feature

Before implementing:

1. Open an issue describing:
   - Problem statement
   - Proposed design
   - API shape
   - Impact on invariants

2. Discuss design before implementation.

During implementation:

- Implement the smallest viable change.
- Add tests for:
  - Edge cases
  - Invalid states
  - Distributed continuation scenarios
- Update documentation accordingly.

---

## 7. Performance-Sensitive Changes

TraceLM is designed to remain lightweight.

For any change affecting performance:

- Include benchmark output.
- Measure sampled and non-sampled paths.
- Avoid increasing hot-path allocations.

Benchmark command:

```bash
python benchmarks/benchmark_tracing.py
```

---

## 8. Pull Request Guidelines

- Keep commits small and focused.
- Use descriptive commit messages.
- Include reasoning and tradeoffs in PR description.
- Reference related issues.
- Ensure all tests pass.
- Ensure packaging still builds cleanly.

Avoid mixing refactors and feature changes in a single PR.

---

## 9. Roadmap Areas

Contributions are especially welcome in:

- Adaptive sampling strategies
- Async task tracing
- Auto-instrumentation utilities
- OpenTelemetry HTTP exporter
- Improved benchmarking suite
- Validation edge-case coverage

---

## 10. Scope Boundaries

TraceLM intentionally does NOT aim to:

- Replace OpenTelemetry
- Become a full observability platform
- Add heavy runtime dependencies
- Introduce complex plugin systems

Keep the core minimal.

---

## 11. License

By contributing, you agree that your contributions will be licensed under the MIT License.

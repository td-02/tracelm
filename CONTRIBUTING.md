# Contributing to TraceLM

## 1. Introduction
Thank you for contributing to TraceLM.

TraceLM is a distributed LLM execution tracer and profiler focused on infrastructure-level visibility for multi-step AI systems. The project goals are to provide reliable tracing, profiling, and propagation primitives that are easy to integrate and safe to operate in production-like environments.

Core philosophy:
- Clean infrastructure abstractions
- Minimal dependencies
- Correctness first

## 2. Development Setup
1. Clone the repository:
   ```bash
   git clone https://github.com/td-02/tracelm.git
   cd tracelm
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # Linux/macOS
   source venv/bin/activate
   # Windows (PowerShell)
   .\venv\Scripts\Activate.ps1
   ```
3. Install in editable mode:
   ```bash
   pip install -e .
   ```
4. Run tests (if available):
   ```bash
   pytest
   ```
5. Run benchmarks:
   ```bash
   python benchmarks/benchmark_tracing.py
   ```

## 3. Project Structure Overview
- `tracelm/`: core tracing and profiling engine
- `tracelm/integrations/`: framework/library integrations (FastAPI, requests)
- `tracelm/distributed/`: distributed tracing helpers (W3C trace context)
- `tracelm/exporters/`: export formats (Chrome trace, OTel JSON)
- `tracelm/bridges/`: runtime bridges (OpenTelemetry SDK bridge)
- `benchmarks/`: performance measurement scripts

## 4. Code Guidelines
- Use type hints in all new and modified code.
- Avoid unnecessary dependencies; prefer standard library first.
- Do not add logging inside core engine paths unless explicitly required.
- Follow W3C trace context rules for trace/span IDs and propagation.
- Preserve distributed-safe invariants:
  - valid single-entry local/distributed trace structure
  - stable parent-child relationships
  - deterministic validation behavior

## 5. How to Add a Feature
1. Open an issue describing the problem and proposed approach.
2. Discuss design and API shape before implementation.
3. Implement the smallest viable change.
4. Add or update tests for behavior and edge cases.
5. Update documentation (README, usage examples, integration notes).

## 6. Pull Request Guidelines
- Keep commits small and focused.
- Use clear, descriptive commit messages.
- Include rationale and design tradeoffs in the PR description.
- Include benchmark evidence for performance-sensitive changes.

## 7. Roadmap Reference
- Adaptive sampling
- Async task tracing
- Auto instrumentation
- OpenTelemetry HTTP exporter

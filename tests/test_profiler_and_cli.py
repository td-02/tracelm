from __future__ import annotations

import io
import json
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from tracelm.cli.main import _cmd_analyze, _cmd_demo, _cmd_export, _cmd_latest
from tracelm.profiler import build_duration_histogram, generate_summary
from tracelm.span import Span
from tracelm.trace import Trace


def _build_trace() -> Trace:
    trace = Trace(trace_id="11111111111111111111111111111111")

    root = Span(
        trace_id=trace.trace_id,
        span_id="1111111111111111",
        parent_id=None,
        name="__root__",
        start_time=0.0,
        end_time=0.2,
        duration=0.2,
    )
    fast = Span(
        trace_id=trace.trace_id,
        span_id="2222222222222222",
        parent_id=root.span_id,
        name="fast_step",
        start_time=0.0,
        end_time=0.0004,
        duration=0.0004,
    )
    slow = Span(
        trace_id=trace.trace_id,
        span_id="3333333333333333",
        parent_id=root.span_id,
        name="slow_step",
        start_time=0.01,
        end_time=0.022,
        duration=0.012,
    )

    trace.add_span(root)
    trace.add_span(fast)
    trace.add_span(slow)
    return trace


class ProfilerAndCliTests(unittest.TestCase):
    def test_build_duration_histogram_counts_spans_in_expected_buckets(self) -> None:
        trace = _build_trace()

        histogram = build_duration_histogram(trace, bucket_bounds_ms=[0.5, 5.0, 10.0])

        self.assertEqual(
            histogram,
            [
                {"label": "0.000-0.500", "lower_ms": 0.0, "upper_ms": 0.5, "count": 1},
                {"label": "0.500-5.000", "lower_ms": 0.5, "upper_ms": 5.0, "count": 0},
                {"label": "5.000-10.000", "lower_ms": 5.0, "upper_ms": 10.0, "count": 0},
                {"label": "> 10.000", "lower_ms": 10.0, "upper_ms": None, "count": 1},
            ],
        )

    def test_generate_summary_includes_histogram(self) -> None:
        trace = _build_trace()

        summary = generate_summary(trace)

        self.assertIn("duration_histogram_ms", summary)
        self.assertTrue(summary["duration_histogram_ms"])
        self.assertEqual(summary["slowest_span"], "slow_step")

    def test_cmd_analyze_prints_human_summary_by_default(self) -> None:
        trace = _build_trace()
        stored_payload = {
            "trace_id": trace.trace_id,
            "root_span_id": trace.root_span_id,
            "spans": {
                span_id: {
                    "trace_id": span.trace_id,
                    "name": span.name,
                    "span_id": span.span_id,
                    "parent_id": span.parent_id,
                    "start_time": span.start_time,
                    "end_time": span.end_time,
                    "duration": span.duration,
                    "tokens_in": span.tokens_in,
                    "tokens_out": span.tokens_out,
                    "cost": span.cost,
                    "error": span.error,
                    "metadata": span.metadata,
                    "children": span.children,
                }
                for span_id, span in trace.spans.items()
            },
        }

        output = io.StringIO()
        with patch("tracelm.cli.main.load_trace", return_value=stored_payload):
            with redirect_stdout(output):
                _cmd_analyze(trace.trace_id)

        rendered = output.getvalue()
        self.assertIn("Trace Summary", rendered)
        self.assertIn("Duration Histogram (ms)", rendered)
        self.assertIn("Execution Tree", rendered)
        self.assertIn("slow_step", rendered)

    def test_cmd_analyze_can_still_emit_raw_json(self) -> None:
        payload = {"trace_id": "abc", "spans": {}}

        output = io.StringIO()
        with patch("tracelm.cli.main.load_trace", return_value=payload):
            with redirect_stdout(output):
                _cmd_analyze("abc", as_json=True)

        self.assertEqual(output.getvalue().strip(), json.dumps(payload))

    def test_cmd_latest_uses_latest_alias(self) -> None:
        trace = _build_trace()
        stored_payload = {
            "trace_id": trace.trace_id,
            "root_span_id": trace.root_span_id,
            "spans": {},
        }

        output = io.StringIO()
        with patch("tracelm.cli.main.latest_trace_id", return_value=trace.trace_id):
            with patch("tracelm.cli.main.load_trace", return_value=stored_payload):
                with redirect_stdout(output):
                    _cmd_latest()

        rendered = output.getvalue()
        self.assertIn("Trace Summary", rendered)
        self.assertIn(trace.trace_id, rendered)

    def test_cmd_export_supports_latest_alias(self) -> None:
        payload = {"trace_id": "abc", "spans": {}}

        with patch("tracelm.cli.main.latest_trace_id", return_value="abc"):
            with patch("tracelm.cli.main.load_trace", return_value=payload):
                with patch("tracelm.cli.main.export_trace_to_chrome") as export_mock:
                    output = io.StringIO()
                    with redirect_stdout(output):
                        _cmd_export("latest", "chrome")

        export_mock.assert_called_once()
        self.assertIn("trace_abc.json", output.getvalue())

    def test_cmd_demo_saves_trace_and_prints_summary(self) -> None:
        output = io.StringIO()
        with patch("tracelm.cli.main.save_trace") as save_mock:
            with redirect_stdout(output):
                _cmd_demo()

        save_mock.assert_called_once()
        rendered = output.getvalue()
        self.assertIn("Trace Summary", rendered)
        self.assertIn("Execution Tree", rendered)
        self.assertIn("llm_call", rendered)


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import json
import sqlite3
import time
from typing import Any, Dict, List, Optional

from tracelm.trace import Trace

DB_FILE = "tracelm_traces.db"


def init_db() -> None:
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS traces(
                trace_id TEXT PRIMARY KEY,
                timestamp REAL,
                data TEXT
            )
            """
        )
        conn.commit()


def _span_to_json_dict(span: Any) -> Dict[str, Any]:
    try:
        return json.loads(json.dumps(vars(span)))
    except TypeError:
        fallback = {slot: getattr(span, slot) for slot in getattr(span, "__slots__", [])}
        return json.loads(json.dumps(fallback))


def save_trace(trace: Trace) -> None:
    init_db()
    spans_payload = {span_id: _span_to_json_dict(span) for span_id, span in trace.spans.items()}
    payload = {
        "trace_id": trace.trace_id,
        "root_span_id": trace.root_span_id,
        "spans": spans_payload,
    }

    with sqlite3.connect(DB_FILE) as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO traces(trace_id, timestamp, data)
            VALUES(?, ?, ?)
            """,
            (trace.trace_id, time.time(), json.dumps(payload)),
        )
        conn.commit()


def load_trace(trace_id: str) -> dict | None:
    init_db()
    with sqlite3.connect(DB_FILE) as conn:
        row = conn.execute("SELECT data FROM traces WHERE trace_id = ?", (trace_id,)).fetchone()
    if row is None:
        return None
    return json.loads(row[0])


def list_traces() -> List[str]:
    init_db()
    with sqlite3.connect(DB_FILE) as conn:
        rows = conn.execute("SELECT trace_id FROM traces ORDER BY timestamp DESC").fetchall()
    return [str(row[0]) for row in rows]


def latest_trace_id() -> Optional[str]:
    traces = list_traces()
    if not traces:
        return None
    return traces[0]

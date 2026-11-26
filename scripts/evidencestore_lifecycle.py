"""Gated lifecycle receipts shared by vLLM, LMCache, and the smoke driver."""

import json
import os
from pathlib import Path
from threading import Lock
import time


TRACE_DIR = os.environ.get("EVIDENCESTORE_LIFECYCLE_TRACE_DIR")
WORKER = os.environ.get("EVIDENCESTORE_LIFECYCLE_WORKER", "unknown")
MODE = os.environ.get("EVIDENCESTORE_LIFECYCLE_MODE")
_lock = Lock()


def enabled():
    return bool(TRACE_DIR)


def emit(event, **fields):
    if not TRACE_DIR:
        return
    pid = os.getpid()
    path = Path(TRACE_DIR) / f"{WORKER}-{pid}.jsonl"
    with _lock, path.open("a", encoding="utf-8") as stream:
        row = {
            **fields,
            "event": event,
            "ts_ns": time.monotonic_ns(),
            "wall_ns": time.time_ns(),
            "pid": pid,
            "worker": WORKER,
            "mode": MODE,
        }
        stream.write(json.dumps(row, separators=(",", ":"), allow_nan=False) + "\n")

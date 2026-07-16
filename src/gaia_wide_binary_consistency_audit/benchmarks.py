"""Runtime/memory benchmarking of the pipeline, written to results/benchmarks.json."""
from __future__ import annotations

import json
import time
import tracemalloc
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable


@dataclass(frozen=True)
class BenchmarkResult:
    label: str
    wall_time_seconds: float
    peak_memory_bytes: int
    n_items: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "wall_time_seconds": self.wall_time_seconds,
            "peak_memory_bytes": self.peak_memory_bytes,
            "n_items": self.n_items,
        }


def benchmark_callable(label: str, fn: Callable[[], Any], n_items: int) -> BenchmarkResult:
    """Time and peak-memory-profile a zero-argument callable."""
    tracemalloc.start()
    start = time.perf_counter()
    fn()
    elapsed = time.perf_counter() - start
    _current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return BenchmarkResult(
        label=label, wall_time_seconds=float(elapsed), peak_memory_bytes=int(peak), n_items=n_items
    )


def write_benchmarks(path: str | Path, results: list[BenchmarkResult]) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps([r.to_dict() for r in results], indent=2), encoding="utf-8")

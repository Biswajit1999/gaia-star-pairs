from __future__ import annotations

import json

from gaia_wide_binary_consistency_audit.benchmarks import benchmark_callable, write_benchmarks


def test_benchmark_callable_measures_time_and_memory():
    def work():
        return sum(range(10000))

    result = benchmark_callable("smoke", work, n_items=10000)
    assert result.wall_time_seconds >= 0.0
    assert result.peak_memory_bytes >= 0
    assert result.n_items == 10000


def test_write_benchmarks_roundtrip(tmp_path):
    def work():
        return 1

    result = benchmark_callable("smoke", work, n_items=1)
    out_path = tmp_path / "benchmarks.json"
    write_benchmarks(out_path, [result])
    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert payload[0]["label"] == "smoke"
    assert payload[0]["n_items"] == 1

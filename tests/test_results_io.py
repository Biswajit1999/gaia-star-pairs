from __future__ import annotations

import json

import pytest

from gaia_wide_binary_consistency_audit.exceptions import DataSchemaError
from gaia_wide_binary_consistency_audit.results_io import Metric, validate_summary, write_summary


def test_write_summary_roundtrip(tmp_path):
    path = tmp_path / "summary.json"
    metrics = [Metric(name="frac_bad", estimate=0.1, units="fraction", sample_size=30)]
    payload = write_summary(
        path, project="p", data_kind="synthetic_demo", metrics=metrics, provenance={"git_commit": "abc"},
        warnings=["w1"],
    )
    on_disk = json.loads(path.read_text(encoding="utf-8"))
    assert on_disk == payload
    assert on_disk["metrics"][0]["name"] == "frac_bad"


def test_validate_summary_missing_key_raises():
    with pytest.raises(DataSchemaError):
        validate_summary({"project": "p"})


def test_validate_summary_metrics_must_be_list():
    with pytest.raises(DataSchemaError):
        validate_summary(
            {"project": "p", "data_kind": "d", "metrics": {}, "provenance": {}, "warnings": []}
        )

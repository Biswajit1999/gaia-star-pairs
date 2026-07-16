from __future__ import annotations

import csv

import numpy as np
import pytest

from gaia_wide_binary_consistency_audit.exceptions import DataSchemaError
from gaia_wide_binary_consistency_audit.io import REQUIRED_COLUMNS, _masked_scalar, load_pair_records


def test_masked_scalar_passthrough():
    assert _masked_scalar(5.0) == 5.0
    assert _masked_scalar(np.ma.masked) is None


def test_load_pair_records_missing_file(tmp_path):
    with pytest.raises(DataSchemaError):
        load_pair_records(tmp_path / "does_not_exist.csv")


def test_load_pair_records_missing_columns(tmp_path):
    path = tmp_path / "bad.csv"
    path.write_text("pair_id,source_id_a\nP1,S1\n", encoding="utf-8")
    with pytest.raises(DataSchemaError):
        load_pair_records(path)


def test_load_pair_records_empty_data_rows(tmp_path):
    path = tmp_path / "headers_only.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(REQUIRED_COLUMNS))
        writer.writeheader()
    with pytest.raises(DataSchemaError):
        load_pair_records(path)


def test_load_pair_records_roundtrip(tmp_path):
    path = tmp_path / "good.csv"
    row = {c: "1.0" for c in REQUIRED_COLUMNS}
    row["pair_id"] = "P1"
    row["source_id_a"] = "A1"
    row["source_id_b"] = "B1"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerow(row)
    records = load_pair_records(path)
    assert len(records) == 1
    assert records[0].pair_id == "P1"
    assert records[0].parallax_a == 1.0


def test_load_pair_records_malformed_numeric(tmp_path):
    path = tmp_path / "malformed.csv"
    row = {c: "1.0" for c in REQUIRED_COLUMNS}
    row["pair_id"] = "P1"
    row["parallax_a"] = "not_a_number"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerow(row)
    with pytest.raises(DataSchemaError):
        load_pair_records(path)

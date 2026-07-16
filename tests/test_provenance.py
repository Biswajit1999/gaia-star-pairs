from __future__ import annotations

import pytest

from gaia_wide_binary_consistency_audit.exceptions import ProvenanceError
from gaia_wide_binary_consistency_audit.provenance import (
    ManifestRow,
    append_manifest_row,
    get_git_commit,
    read_manifest,
    sha256_bytes,
    sha256_file,
)


def test_sha256_file_matches_bytes(tmp_path):
    path = tmp_path / "data.txt"
    path.write_bytes(b"hello world")
    assert sha256_file(path) == sha256_bytes(b"hello world")


def test_get_git_commit_never_raises(tmp_path):
    # tmp_path is not a git repo; must return the sentinel, not raise.
    result = get_git_commit(tmp_path)
    assert isinstance(result, str)
    assert result != ""


def test_append_and_read_manifest_roundtrip(tmp_path):
    path = tmp_path / "manifest.csv"
    row = ManifestRow(
        product_id="p1", source="s", source_url="https://example.test", retrieved_utc="2026-07-15T00:00:00Z",
        sha256="abc123", file_size_bytes=10, selection_reason="test", licence_or_terms="CC-BY-4.0",
    )
    append_manifest_row(path, row)
    rows = read_manifest(path)
    assert len(rows) == 1
    assert rows[0]["product_id"] == "p1"


def test_read_manifest_missing_file_raises(tmp_path):
    with pytest.raises(ProvenanceError):
        read_manifest(tmp_path / "nope.csv")

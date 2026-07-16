"""Data loading for wide-binary pair astrometry.

Pure, testable I/O: reading the pair-level CSV (either the demo dataset in
data/example/demo.csv or the real fetched sample in data/processed/) into
`PairRecord` objects, and the live network query functions used by
scripts/fetch_data.py to build that CSV in the first place. Network
functions are isolated here (not duplicated between fetch_data.py and
run_analysis.py) exactly as in
euclid-q1-vis-psf-astrometry-audit/src/.../gaia_match.py.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from gaia_wide_binary_consistency_audit.exceptions import ArchiveAccessError, DataSchemaError

REQUIRED_COLUMNS = (
    "pair_id", "source_id_a", "source_id_b",
    "parallax_a", "parallax_a_error", "parallax_b", "parallax_b_error",
    "pmra_a", "pmra_a_error", "pmra_b", "pmra_b_error",
    "pmdec_a", "pmdec_a_error", "pmdec_b", "pmdec_b_error",
    "mean_g_mag", "separation_arcsec", "ruwe_a", "ruwe_b",
)


@dataclass(frozen=True)
class PairRecord:
    pair_id: str
    source_id_a: str
    source_id_b: str
    parallax_a: float
    parallax_a_error: float
    parallax_b: float
    parallax_b_error: float
    pmra_a: float
    pmra_a_error: float
    pmra_b: float
    pmra_b_error: float
    pmdec_a: float
    pmdec_a_error: float
    pmdec_b: float
    pmdec_b_error: float
    mean_g_mag: float
    separation_arcsec: float
    ruwe_a: float
    ruwe_b: float


def _masked_scalar(value):
    """Return None for a masked/NULL TAP result cell, else the raw value.

    Real Gaia TAP query results can have NULL ruwe/parallax_error entries
    (e.g. a source with an unreliable 2-parameter-only solution) --
    astropy represents this as a numpy masked constant, not Python None, so
    a naive `value is not None` check silently fails to catch it (the same
    bug found and fixed in euclid-q1-vis-psf-astrometry-audit/fetch_data.py).
    """
    return None if np.ma.is_masked(value) else value


def load_pair_records(path: str | Path) -> list[PairRecord]:
    """Load pair-level astrometry from a CSV matching REQUIRED_COLUMNS.

    Raises DataSchemaError for a missing file, missing required columns, or
    a row with a non-numeric/empty value in a required numeric column
    (rather than silently coercing to NaN and letting a later stage produce
    a misleading result).
    """
    csv_path = Path(path)
    if not csv_path.exists():
        raise DataSchemaError(f"pair records file not found: {csv_path}")

    with csv_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise DataSchemaError(f"{csv_path} has no header row")
        missing = [c for c in REQUIRED_COLUMNS if c not in reader.fieldnames]
        if missing:
            raise DataSchemaError(f"{csv_path} missing required columns: {missing}")

        records: list[PairRecord] = []
        for i, row in enumerate(reader):
            try:
                records.append(
                    PairRecord(
                        pair_id=row["pair_id"],
                        source_id_a=row["source_id_a"],
                        source_id_b=row["source_id_b"],
                        parallax_a=float(row["parallax_a"]),
                        parallax_a_error=float(row["parallax_a_error"]),
                        parallax_b=float(row["parallax_b"]),
                        parallax_b_error=float(row["parallax_b_error"]),
                        pmra_a=float(row["pmra_a"]),
                        pmra_a_error=float(row["pmra_a_error"]),
                        pmra_b=float(row["pmra_b"]),
                        pmra_b_error=float(row["pmra_b_error"]),
                        pmdec_a=float(row["pmdec_a"]),
                        pmdec_a_error=float(row["pmdec_a_error"]),
                        pmdec_b=float(row["pmdec_b"]),
                        pmdec_b_error=float(row["pmdec_b_error"]),
                        mean_g_mag=float(row["mean_g_mag"]),
                        separation_arcsec=float(row["separation_arcsec"]),
                        ruwe_a=float(row["ruwe_a"]),
                        ruwe_b=float(row["ruwe_b"]),
                    )
                )
            except (KeyError, ValueError) as exc:
                raise DataSchemaError(f"{csv_path} row {i}: malformed pair record: {exc}") from exc

    if not records:
        raise DataSchemaError(f"{csv_path} contains a header but zero data rows")
    return records


def query_vizier_wide_binary_sample(n_rows: int, catalog_id: str = "J/ApJ/934/148/tablea1"):
    """Live, row-limited VizieR query for a deterministic sample of wide
    binary candidate pairs (Gaia source IDs of both components, separation,
    chance-alignment probability).

    NOTE: the originally-planned catalogue (El-Badry, Rix & Heintz 2021,
    J/MNRAS/506/2269) is NOT actually present in VizieR's TAP_SCHEMA (live
    query for that table_name returns zero results; confirmed directly
    against tapvizier.cds.unistra.fr in this session) -- only the full
    Zenodo deposit (10.5281/zenodo.4435257, too large for this bounded
    audit) exists for that specific paper. The default catalogue here is
    instead Heintz, Hermes, El-Badry et al. (2023 erratum), "The full
    catalog of wide double white dwarf pairs", ApJ 934, 148 (VizieR
    J/ApJ/934/148/tablea1) -- a real, live-verified, directly relevant
    wide-binary Gaia astrometry catalogue (same co-moving-pair consistency
    question, white dwarf pairs instead of the general stellar sample).

    Isolated network I/O so it can be mocked/skipped in tests; the only
    caller in real-data mode is scripts/fetch_data.py.
    """
    from astroquery.vizier import Vizier

    vizier = Vizier(row_limit=n_rows, columns=["GaiaPrim", "GaiaSec", "Sep", "Chance"])
    try:
        result = vizier.get_catalogs(catalog_id)
    except Exception as exc:  # noqa: BLE001
        raise ArchiveAccessError(f"VizieR query for {catalog_id} failed: {exc}") from exc
    if not result:
        raise ArchiveAccessError(f"VizieR catalogue {catalog_id} returned no tables")
    table = result[0]
    if len(table) == 0:
        raise ArchiveAccessError(f"VizieR catalogue {catalog_id} query returned zero rows")
    return table


def query_gaia_dr3_sources(source_ids: list[int]):
    """Live Gaia DR3 TAP query for parallax/pm astrometry + uncertainties +
    RUWE + g_mag for a specific list of source_id values.

    Column access downstream must be case-insensitive: the Gaia archive TAP
    service returns SOURCE_ID etc. in its own casing regardless of the
    SELECT clause casing (same behaviour documented and handled in
    euclid-q1-vis-psf-astrometry-audit's gaia_match.py).
    """
    from astroquery.gaia import Gaia

    if not source_ids:
        raise ArchiveAccessError("no source_ids provided for Gaia DR3 query")
    ids_clause = ",".join(str(int(s)) for s in source_ids)
    query = (
        "SELECT source_id, parallax, parallax_error, pmra, pmra_error, "
        "pmdec, pmdec_error, phot_g_mean_mag, ruwe FROM gaiadr3.gaia_source "
        f"WHERE source_id IN ({ids_clause})"
    )
    try:
        job = Gaia.launch_job(query)
        table = job.get_results()
    except Exception as exc:  # noqa: BLE001
        raise ArchiveAccessError(f"Gaia DR3 source query failed: {exc}") from exc
    if len(table) == 0:
        raise ArchiveAccessError("Gaia DR3 source query returned zero rows for requested source_ids")
    return table


def gaia_column(table, name: str):
    """Case-insensitive column lookup for a Gaia/VizieR astropy Table."""
    columns_lower = {c.lower(): c for c in table.colnames}
    key = name.lower()
    if key not in columns_lower:
        raise DataSchemaError(f"expected column '{name}' not found (have: {table.colnames})")
    return table[columns_lower[key]]

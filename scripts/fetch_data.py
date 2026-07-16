"""Real-data fetch: a small, deterministic sample of El-Badry, Rix & Heintz
(2021) Gaia EDR3 wide-binary candidates, cross-matched against live Gaia DR3
astrometry for each component.

Gated behind --i-have-authorization per docs/VALIDATION_CONTRACT.md. Two live network
calls: VizieR (astroquery.vizier) for the wide-binary candidate list, then
astroquery.gaia for authoritative DR3 parallax/pm/uncertainty/RUWE for every
component source_id. Writes data/processed/real_pairs.csv (input to
run_analysis.py --real) and appends to data/manifest.csv plus
data/source_catalog.csv (catalogue-derived, not a single downloadable file,
so it does not fit the single-product manifest schema -- see
euclid-q1-vis-psf-astrometry-audit's identical pattern).
"""
from __future__ import annotations

import argparse
import csv
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gaia_wide_binary_consistency_audit.exceptions import ArchiveAccessError  # noqa: E402
from gaia_wide_binary_consistency_audit.io import (  # noqa: E402
    _masked_scalar,
    gaia_column,
    query_gaia_dr3_sources,
    query_vizier_wide_binary_sample,
)
from gaia_wide_binary_consistency_audit.provenance import (  # noqa: E402
    ManifestRow,
    append_manifest_row,
    sha256_file,
)

VIZIER_CATALOG_ID = "J/ApJ/934/148/tablea1"
SOURCE_URL = "https://vizier.cds.unistra.fr/viz-bin/VizieR-3?-source=J/ApJ/934/148"
LICENCE_TERMS = (
    "Heintz, Hermes, El-Badry et al. (2023 erratum) ApJ 934, 148, VizieR "
    "catalogue J/ApJ/934/148/tablea1 (CDS Strasbourg); Gaia DR3 astrometry "
    "via astroquery.gaia (ESA Gaia archive), Gaia data access rights, "
    "https://www.cosmos.esa.int/web/gaia-users/license"
)
SOURCE_CATALOG_COLUMNS = (
    "pair_id", "source_id_a", "source_id_b", "sep_au", "r_chance_align",
)
OUTPUT_COLUMNS = (
    "pair_id", "source_id_a", "source_id_b",
    "parallax_a", "parallax_a_error", "parallax_b", "parallax_b_error",
    "pmra_a", "pmra_a_error", "pmra_b", "pmra_b_error",
    "pmdec_a", "pmdec_a_error", "pmdec_b", "pmdec_b_error",
    "mean_g_mag", "separation_arcsec", "ruwe_a", "ruwe_b",
)


def _row_to_dict(table, i: int) -> dict:
    return {name: table[name][i] for name in table.colnames}


def _lookup_component(gaia_table, source_id: int) -> dict:
    ids = np.array(gaia_column(gaia_table, "source_id"), dtype=np.int64)
    matches = np.where(ids == int(source_id))[0]
    if matches.size == 0:
        raise ArchiveAccessError(f"Gaia DR3 cross-match missing source_id {source_id}")
    i = int(matches[0])
    return {
        "parallax": float(_masked_scalar(gaia_column(gaia_table, "parallax")[i]) or np.nan),
        "parallax_error": float(_masked_scalar(gaia_column(gaia_table, "parallax_error")[i]) or np.nan),
        "pmra": float(_masked_scalar(gaia_column(gaia_table, "pmra")[i]) or np.nan),
        "pmra_error": float(_masked_scalar(gaia_column(gaia_table, "pmra_error")[i]) or np.nan),
        "pmdec": float(_masked_scalar(gaia_column(gaia_table, "pmdec")[i]) or np.nan),
        "pmdec_error": float(_masked_scalar(gaia_column(gaia_table, "pmdec_error")[i]) or np.nan),
        "phot_g_mean_mag": float(_masked_scalar(gaia_column(gaia_table, "phot_g_mean_mag")[i]) or np.nan),
        "ruwe": float(_masked_scalar(gaia_column(gaia_table, "ruwe")[i]) or np.nan),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--i-have-authorization", action="store_true", required=True)
    parser.add_argument("--n-pairs", type=int, default=30)
    parser.add_argument("--manifest", type=Path, default=Path("data/manifest.csv"))
    parser.add_argument("--source-catalog", type=Path, default=Path("data/source_catalog.csv"))
    parser.add_argument("--output", type=Path, default=Path("data/processed/real_pairs.csv"))
    args = parser.parse_args()

    print(f"Querying VizieR {VIZIER_CATALOG_ID} for {args.n_pairs} wide-binary candidates...")
    vizier_table = query_vizier_wide_binary_sample(args.n_pairs, catalog_id=VIZIER_CATALOG_ID)
    print(f"VizieR returned {len(vizier_table)} candidate rows.")

    source1_col = gaia_column(vizier_table, "GaiaPrim")
    source2_col = gaia_column(vizier_table, "GaiaSec")
    sep_col = gaia_column(vizier_table, "Sep")
    rca_col = gaia_column(vizier_table, "Chance")

    all_source_ids: list[int] = []
    for i in range(len(vizier_table)):
        all_source_ids.append(int(source1_col[i]))
        all_source_ids.append(int(source2_col[i]))
    unique_ids = sorted(set(all_source_ids))

    print(f"Cross-matching {len(unique_ids)} unique Gaia DR3 source_ids...")
    gaia_table = query_gaia_dr3_sources(unique_ids)
    print(f"Gaia DR3 query returned {len(gaia_table)} rows.")

    source_catalog_rows = []
    output_rows = []
    n_ok, n_skipped = 0, 0
    for i in range(len(vizier_table)):
        pair_id = f"WB{i:04d}"
        sid_a, sid_b = int(source1_col[i]), int(source2_col[i])
        try:
            comp_a = _lookup_component(gaia_table, sid_a)
            comp_b = _lookup_component(gaia_table, sid_b)
            required = [
                comp_a["parallax"], comp_a["parallax_error"], comp_b["parallax"], comp_b["parallax_error"],
                comp_a["pmra"], comp_a["pmra_error"], comp_b["pmra"], comp_b["pmra_error"],
                comp_a["pmdec"], comp_a["pmdec_error"], comp_b["pmdec"], comp_b["pmdec_error"],
                comp_a["ruwe"], comp_b["ruwe"],
            ]
            if not all(np.isfinite(v) for v in required):
                raise ArchiveAccessError(f"pair {pair_id}: NULL astrometry field in Gaia cross-match")
        except ArchiveAccessError as exc:
            print(f"  skipping {pair_id}: {exc}")
            n_skipped += 1
            continue

        mean_g = np.nanmean([comp_a["phot_g_mean_mag"], comp_b["phot_g_mean_mag"]])
        sep_au = float(_masked_scalar(sep_col[i]) or np.nan)
        # Convert AU separation to angular separation using the mean parallax
        # (distance_pc = 1000/parallax_mas -> sep_arcsec = sep_au / distance_pc).
        mean_plx = np.nanmean([comp_a["parallax"], comp_b["parallax"]])
        distance_pc = 1000.0 / mean_plx if mean_plx > 0 else np.nan
        sep_arcsec = sep_au / distance_pc if distance_pc and np.isfinite(distance_pc) else np.nan
        if not np.isfinite(sep_arcsec):
            n_skipped += 1
            continue

        output_rows.append({
            "pair_id": pair_id, "source_id_a": sid_a, "source_id_b": sid_b,
            "parallax_a": comp_a["parallax"], "parallax_a_error": comp_a["parallax_error"],
            "parallax_b": comp_b["parallax"], "parallax_b_error": comp_b["parallax_error"],
            "pmra_a": comp_a["pmra"], "pmra_a_error": comp_a["pmra_error"],
            "pmra_b": comp_b["pmra"], "pmra_b_error": comp_b["pmra_error"],
            "pmdec_a": comp_a["pmdec"], "pmdec_a_error": comp_a["pmdec_error"],
            "pmdec_b": comp_b["pmdec"], "pmdec_b_error": comp_b["pmdec_error"],
            "mean_g_mag": float(mean_g), "separation_arcsec": float(sep_arcsec),
            "ruwe_a": comp_a["ruwe"], "ruwe_b": comp_b["ruwe"],
        })
        source_catalog_rows.append({
            "pair_id": pair_id, "source_id_a": sid_a, "source_id_b": sid_b,
            "sep_au": sep_au, "r_chance_align": float(_masked_scalar(rca_col[i]) or np.nan),
        })
        n_ok += 1

    if n_ok == 0:
        raise ArchiveAccessError("no wide-binary pairs had a complete Gaia DR3 cross-match")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(OUTPUT_COLUMNS))
        writer.writeheader()
        writer.writerows(output_rows)

    args.source_catalog.parent.mkdir(parents=True, exist_ok=True)
    with args.source_catalog.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(SOURCE_CATALOG_COLUMNS))
        writer.writeheader()
        writer.writerows(source_catalog_rows)

    file_sha = sha256_file(args.output)
    file_size = args.output.stat().st_size
    append_manifest_row(
        args.manifest,
        ManifestRow(
            product_id="wide_binary_real_sample_v1",
            source="VizieR J/MNRAS/506/2269 + Gaia DR3 (gaiadr3.gaia_source)",
            source_url=SOURCE_URL,
            retrieved_utc=datetime.now(timezone.utc).isoformat(),
            sha256=file_sha,
            file_size_bytes=file_size,
            selection_reason=(
                f"deterministic row-limited VizieR sample (n_pairs={args.n_pairs}), "
                f"cross-matched against live Gaia DR3 TAP; {n_ok} pairs retained, "
                f"{n_skipped} skipped for incomplete astrometry"
            ),
            licence_or_terms=LICENCE_TERMS,
        ),
    )
    print(f"Wrote {n_ok} real wide-binary pairs to {args.output} ({n_skipped} skipped).")
    print(f"Manifest updated: {args.manifest}")


if __name__ == "__main__":
    main()

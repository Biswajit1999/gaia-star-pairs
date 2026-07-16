from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gaia_wide_binary_consistency_audit.benchmarks import benchmark_callable, write_benchmarks  # noqa: E402
from gaia_wide_binary_consistency_audit.core import run_pipeline  # noqa: E402
from gaia_wide_binary_consistency_audit.io import load_pair_records  # noqa: E402
from gaia_wide_binary_consistency_audit.provenance import get_git_commit, sha256_config  # noqa: E402
from gaia_wide_binary_consistency_audit.results_io import Metric, write_summary  # noqa: E402
from gaia_wide_binary_consistency_audit.synthetic import generate_demo_dataset  # noqa: E402

PROJECT_NAME = "gaia-wide-binary-consistency-audit"
REPO_ROOT = Path(__file__).resolve().parents[1]


def _summarize_and_write(records, data_kind: str, config_path: Path) -> dict:
    result = run_pipeline(records)

    def _run():
        return run_pipeline(records)

    bench = benchmark_callable(f"run_pipeline[{data_kind}]", _run, n_items=len(records))
    write_benchmarks(REPO_ROOT / "results" / "benchmarks.json", [bench])

    metrics = [
        Metric(
            name="fraction_inconsistent",
            estimate=result.fraction_inconsistent,
            units="fraction",
            sample_size=result.n_processed,
        ),
        Metric(
            name="n_pairs_processed",
            estimate=float(result.n_processed),
            units="count",
            sample_size=result.n_processed,
        ),
    ]
    for scale in result.magnitude_bin_scales:
        metrics.append(
            Metric(
                name=f"rms_z_combined__magnitude__{scale.bin_label}",
                estimate=scale.rms_z_combined,
                units="dimensionless (sigma)",
                sample_size=scale.n_pairs,
            )
        )
    for scale in result.separation_bin_scales:
        metrics.append(
            Metric(
                name=f"rms_z_combined__separation__{scale.bin_label}",
                estimate=scale.rms_z_combined,
                units="dimensionless (sigma)",
                sample_size=scale.n_pairs,
            )
        )
    for scale in result.quality_bin_scales:
        metrics.append(
            Metric(
                name=f"rms_z_combined__quality__{scale.bin_label}",
                estimate=scale.rms_z_combined,
                units="dimensionless (sigma)",
                sample_size=scale.n_pairs,
            )
        )

    provenance = {
        "git_commit": get_git_commit(REPO_ROOT),
        "config_sha256": sha256_config(config_path) if config_path.exists() else "N/A",
        "data_kind": data_kind,
    }

    payload = write_summary(
        REPO_ROOT / "results" / "summary.json",
        project=PROJECT_NAME,
        data_kind=data_kind,
        metrics=metrics,
        provenance=provenance,
        warnings=result.warnings,
    )
    (REPO_ROOT / "results" / "warnings.json").write_text(
        json.dumps(result.warnings, indent=2), encoding="utf-8"
    )
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--demo", action="store_true", help="Run on synthetic demo data")
    parser.add_argument("--real", action="store_true", help="Run on real fetched data")
    parser.add_argument(
        "--real-input", type=Path, default=Path("data/processed/real_pairs.csv"),
        help="Path to real pair-record CSV produced by scripts/fetch_data.py",
    )
    parser.add_argument("--config", type=Path, default=Path("config/analysis.yml"))
    args = parser.parse_args()

    if not args.demo and not args.real:
        raise SystemExit("Specify --demo or --real")

    if args.real:
        if not args.real_input.exists():
            raise SystemExit(
                f"Real input {args.real_input} not found; run scripts/fetch_data.py --i-have-authorization first"
            )
        records = load_pair_records(args.real_input)
        payload = _summarize_and_write(records, data_kind="real_gaia_dr3_wide_binary_sample", config_path=args.config)
    else:
        records = generate_demo_dataset()
        payload = _summarize_and_write(records, data_kind="synthetic_demo", config_path=args.config)

    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()

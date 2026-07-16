from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np  # noqa: E402

from gaia_wide_binary_consistency_audit.core import demo_series, run_pipeline  # noqa: E402
from gaia_wide_binary_consistency_audit.io import load_pair_records  # noqa: E402
from gaia_wide_binary_consistency_audit.plotting import (  # noqa: E402
    fig_normalized_residuals,
    fig_scale_vs_magnitude,
    fig_selection_flow,
    fig_separation_sensitivity,
    fig_synthetic_recovery,
    plot_demo,
)
from gaia_wide_binary_consistency_audit.provenance import get_git_commit, sha256_config  # noqa: E402
from gaia_wide_binary_consistency_audit.synthetic import generate_demo_dataset, generate_synthetic_pairs  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[1]
FIGURES_DIR = REPO_ROOT / "figures"


def _sidecar(base_path: Path, config_path: Path, extra: dict) -> None:
    payload = {
        "git_commit": get_git_commit(REPO_ROOT),
        "config_sha256": sha256_config(config_path) if config_path.exists() else "N/A",
        **extra,
    }
    base_path.with_suffix(".json").write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _make_figures(records, tag: str, config_path: Path) -> None:
    result = run_pipeline(records)

    stage_counts = {
        "input_pairs": result.n_input,
        "processed_pairs": result.n_processed,
        "excluded": result.n_input - result.n_processed,
    }
    base = FIGURES_DIR / f"fig01_selection_flow_{tag}"
    svg, _ = fig_selection_flow(stage_counts, base)
    _sidecar(base, config_path, {"figure": "selection_flow", "stage_counts": stage_counts})

    base = FIGURES_DIR / f"fig02_normalized_residuals_{tag}"
    svg, _ = fig_normalized_residuals(result.consistency_results, base)
    _sidecar(base, config_path, {"figure": "normalized_residuals", "n_pairs": result.n_processed})

    base = FIGURES_DIR / f"fig03_scale_vs_magnitude_{tag}"
    svg, _ = fig_scale_vs_magnitude(result.magnitude_bin_scales, base)
    _sidecar(
        base, config_path,
        {"figure": "scale_vs_magnitude", "bins": [b.bin_label for b in result.magnitude_bin_scales]},
    )

    base = FIGURES_DIR / f"fig04_separation_sensitivity_{tag}"
    svg, _ = fig_separation_sensitivity(result.separation_bin_scales, base)
    _sidecar(
        base, config_path,
        {"figure": "separation_sensitivity", "bins": [b.bin_label for b in result.separation_bin_scales]},
    )


def _make_synthetic_recovery_figure(config_path: Path) -> None:
    injected_scales = np.array([0.5, 1.0, 1.5, 2.0, 3.0, 4.0])
    recovered_scales = []
    for scale in injected_scales:
        pairs = generate_synthetic_pairs(40, seed=20260713, scale_factor=float(scale))
        result = run_pipeline([p.record for p in pairs])
        combined_rms = np.sqrt(
            np.mean(
                [r.z_parallax**2 for r in result.consistency_results]
                + [r.z_pmra**2 for r in result.consistency_results]
                + [r.z_pmdec**2 for r in result.consistency_results]
            )
        )
        recovered_scales.append(float(combined_rms))
    base = FIGURES_DIR / "fig05_synthetic_recovery"
    fig_synthetic_recovery(injected_scales, np.array(recovered_scales), base)
    _sidecar(
        base, config_path,
        {
            "figure": "synthetic_recovery",
            "injected_scales": injected_scales.tolist(),
            "recovered_scales": recovered_scales,
        },
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--demo", action="store_true")
    parser.add_argument("--real", action="store_true")
    parser.add_argument("--real-input", type=Path, default=Path("data/processed/real_pairs.csv"))
    parser.add_argument("--config", type=Path, default=Path("config/analysis.yml"))
    args = parser.parse_args()

    if not args.demo and not args.real:
        plot_demo(demo_series(), FIGURES_DIR / "fig00_smoke_test.png")
        print("Wrote smoke-test figure only. Use --demo or --real for the full figure set.")
        return

    if args.real:
        if not args.real_input.exists():
            raise SystemExit(f"Real input {args.real_input} not found; run scripts/fetch_data.py first")
        records = load_pair_records(args.real_input)
        _make_figures(records, tag="real", config_path=args.config)
    else:
        records = generate_demo_dataset()
        _make_figures(records, tag="demo", config_path=args.config)

    _make_synthetic_recovery_figure(args.config)
    print(f"Figures written to {FIGURES_DIR}")


if __name__ == "__main__":
    main()

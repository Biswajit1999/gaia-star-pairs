"""Figure generation functions for the five required scientific figures
(docs/FIGURE_AND_UI_SPEC.md): selection flow, normalised residuals, scale vs
magnitude, separation sensitivity, synthetic recovery.

Each function draws onto a matplotlib Figure and is saved by the caller
(scripts/make_figures.py) as both SVG and 300 dpi PNG with a sidecar JSON, so
the plotting logic itself stays reusable and independently testable.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import scienceplots  # noqa: F401 - importing registers the SciencePlots styles

from gaia_wide_binary_consistency_audit.residuals import BinScale
from gaia_wide_binary_consistency_audit.statistics import PairConsistency

plt.style.use(["science", "no-latex"])


def plot_demo(values: np.ndarray, output: str | Path) -> Path:
    """Legacy smoke-test plot, kept for `make_figures.py --demo` sanity checks."""
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(np.arange(values.size), values)
    ax.set_xlabel("Synthetic index")
    ax.set_ylabel("Synthetic value")
    ax.set_title("Smoke-test output -- not a scientific result")
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)
    return path


def _save(fig: plt.Figure, base_path: Path) -> tuple[Path, Path]:
    base_path.parent.mkdir(parents=True, exist_ok=True)
    svg_path = base_path.with_suffix(".svg")
    png_path = base_path.with_suffix(".png")
    fig.savefig(svg_path, dpi=180)
    fig.savefig(png_path, dpi=300)
    plt.close(fig)
    return svg_path, png_path


def fig_selection_flow(stage_counts: dict[str, int], base_path: str | Path) -> tuple[Path, Path]:
    """Figure 1: bar chart of sample counts surviving each selection stage."""
    labels = list(stage_counts.keys())
    values = list(stage_counts.values())
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.bar(labels, values, color="#4C72B0")
    ax.set_ylabel("Number of pairs")
    ax.set_title(f"Selection flow (n_final={values[-1] if values else 0})")
    for i, v in enumerate(values):
        ax.text(i, v, str(v), ha="center", va="bottom")
    fig.autofmt_xdate(rotation=20)
    fig.tight_layout()
    return _save(fig, Path(base_path))


def fig_normalized_residuals(results: list[PairConsistency], base_path: str | Path) -> tuple[Path, Path]:
    """Figure 2: histogram of standardized (z-score) residuals vs. the
    expected standard-normal distribution.
    """
    z_all = np.concatenate(
        [[r.z_parallax for r in results], [r.z_pmra for r in results], [r.z_pmdec for r in results]]
    )
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.hist(z_all, bins=20, density=True, alpha=0.7, color="#55A868", label=f"observed (n={len(results)} pairs)")
    xs = np.linspace(-4, 4, 200)
    ax.plot(xs, np.exp(-(xs**2) / 2) / np.sqrt(2 * np.pi), color="black", linestyle="--", label="standard normal")
    ax.set_xlabel("Standardized residual z = delta / sigma_combined")
    ax.set_ylabel("Density")
    ax.set_title("Normalised residuals across parallax, pmra, pmdec")
    ax.legend()
    fig.tight_layout()
    return _save(fig, Path(base_path))


def fig_scale_vs_magnitude(bin_scales: list[BinScale], base_path: str | Path) -> tuple[Path, Path]:
    """Figure 3: empirical residual RMS scale per magnitude bin (should be
    ~1 if quoted uncertainties are well-calibrated).
    """
    labels = [b.bin_label for b in bin_scales]
    values = [b.rms_z_combined for b in bin_scales]
    ns = [b.n_pairs for b in bin_scales]
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.plot(labels, values, "o-", color="#C44E52")
    ax.axhline(1.0, color="black", linestyle=":", label="ideal calibration (scale=1)")
    for i, n in enumerate(ns):
        ax.annotate(f"n={n}", (i, values[i]), textcoords="offset points", xytext=(0, 8), ha="center")
    ax.set_ylabel("RMS standardized residual (combined)")
    ax.set_title("Uncertainty-calibration scale vs. magnitude bin")
    ax.legend()
    fig.tight_layout()
    return _save(fig, Path(base_path))


def fig_separation_sensitivity(bin_scales: list[BinScale], base_path: str | Path) -> tuple[Path, Path]:
    """Figure 4: same scale diagnostic, split by angular-separation bin."""
    labels = [b.bin_label for b in bin_scales]
    values = [b.rms_z_combined for b in bin_scales]
    ns = [b.n_pairs for b in bin_scales]
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.plot(labels, values, "s-", color="#8172B2")
    ax.axhline(1.0, color="black", linestyle=":", label="ideal calibration (scale=1)")
    for i, n in enumerate(ns):
        ax.annotate(f"n={n}", (i, values[i]), textcoords="offset points", xytext=(0, 8), ha="center")
    ax.set_ylabel("RMS standardized residual (combined)")
    ax.set_title("Uncertainty-calibration scale vs. separation bin")
    ax.legend()
    fig.tight_layout()
    return _save(fig, Path(base_path))


def fig_synthetic_recovery(
    injected_scales: np.ndarray, recovered_scales: np.ndarray, base_path: str | Path
) -> tuple[Path, Path]:
    """Figure 5: injection-recovery validation -- recovered empirical scale
    vs. the known injected noise-inflation factor, for synthetic pairs.
    """
    fig, ax = plt.subplots(figsize=(6, 6))
    lo = float(min(injected_scales.min(), recovered_scales.min()))
    hi = float(max(injected_scales.max(), recovered_scales.max()))
    ax.plot([lo, hi], [lo, hi], color="black", linestyle="--", label="1:1")
    ax.scatter(
        injected_scales, recovered_scales, color="#4C72B0",
        label=f"synthetic pairs (n={len(injected_scales)})",
    )
    ax.set_xlabel("Injected true scale factor")
    ax.set_ylabel("Recovered empirical scale (RMS z)")
    ax.set_title("Synthetic scale-recovery validation")
    ax.legend()
    fig.tight_layout()
    return _save(fig, Path(base_path))

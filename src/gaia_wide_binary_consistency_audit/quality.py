"""Magnitude / separation / quality binning for the consistency audit.

Bins follow docs/RESEARCH_BLUEPRINT.md's requirement to check consistency
"across magnitude, separation and quality bins" rather than pooling all
pairs into a single number that could hide systematics in a subset.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from gaia_wide_binary_consistency_audit.exceptions import InsufficientDataError

# Bin edges are deliberately coarse (few pairs per audit sample) and
# documented rather than tuned to the sample at hand.
MAGNITUDE_BIN_EDGES = (0.0, 12.0, 15.0, 18.0, 25.0)
MAGNITUDE_BIN_LABELS = ("G<=12", "12<G<=15", "15<G<=18", "G>18")

SEPARATION_BIN_EDGES_ARCSEC = (0.0, 5.0, 20.0, 60.0, 1e6)
SEPARATION_BIN_LABELS = ("<5as", "5-20as", "20-60as", ">60as")

# RUWE (renormalised unit weight error) is the standard Gaia single-source
# astrometric quality flag; RUWE <~ 1.4 is the commonly used "good solution"
# cut (Lindegren et al. 2021 recommendation, cited in docs/LITERATURE_SEEDS.md
# companion notes).
RUWE_GOOD_THRESHOLD = 1.4


def assign_bin(value: float, edges: tuple[float, ...], labels: tuple[str, ...]) -> str:
    if not np.isfinite(value):
        raise InsufficientDataError(f"cannot bin non-finite value {value}")
    if len(edges) != len(labels) + 1:
        raise ValueError("edges must have exactly one more entry than labels")
    for lo, hi, label in zip(edges[:-1], edges[1:], labels):
        if lo <= value < hi:
            return label
    if value == edges[-1]:
        return labels[-1]
    raise InsufficientDataError(f"value {value} falls outside binning edges {edges}")


def magnitude_bin(mean_g_mag: float) -> str:
    return assign_bin(mean_g_mag, MAGNITUDE_BIN_EDGES, MAGNITUDE_BIN_LABELS)


def separation_bin(separation_arcsec: float) -> str:
    return assign_bin(separation_arcsec, SEPARATION_BIN_EDGES_ARCSEC, SEPARATION_BIN_LABELS)


def quality_flag(ruwe_a: float, ruwe_b: float, threshold: float = RUWE_GOOD_THRESHOLD) -> str:
    """'good' if both components have RUWE below threshold, else 'flagged'."""
    if not (np.isfinite(ruwe_a) and np.isfinite(ruwe_b)):
        raise InsufficientDataError("RUWE values must be finite to assign a quality flag")
    return "good" if (ruwe_a < threshold and ruwe_b < threshold) else "flagged"


@dataclass(frozen=True)
class BinAssignment:
    pair_id: str
    magnitude_bin: str
    separation_bin: str
    quality_flag: str


def assign_pair_bins(
    pair_id: str, mean_g_mag: float, separation_arcsec: float, ruwe_a: float, ruwe_b: float
) -> BinAssignment:
    return BinAssignment(
        pair_id=pair_id,
        magnitude_bin=magnitude_bin(mean_g_mag),
        separation_bin=separation_bin(separation_arcsec),
        quality_flag=quality_flag(ruwe_a, ruwe_b),
    )


def group_by(bin_assignments: list[BinAssignment], key: str) -> dict[str, list[str]]:
    """Group pair_ids by the requested bin key ('magnitude_bin',
    'separation_bin', or 'quality_flag'). Bins with zero members are simply
    absent from the returned dict (never fabricated); callers should treat
    absent keys as "no data in this bin" and report it as a warning rather
    than silently skipping.
    """
    if not bin_assignments:
        raise InsufficientDataError("no bin assignments to group")
    groups: dict[str, list[str]] = {}
    for b in bin_assignments:
        value = getattr(b, key)
        groups.setdefault(value, []).append(b.pair_id)
    return groups

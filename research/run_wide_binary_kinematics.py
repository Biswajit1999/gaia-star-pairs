"""Run conditional Gaia DR3 wide-binary diagnostics on the retained CSV."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from research.wide_binary_kinematics import (
    chi2_components, delta_method_speed_sigma, load_pairs,
    monte_carlo_speed_ratio, projected_kinematics,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=Path, default=Path('data/processed/real_pairs.csv'))
    parser.add_argument('--output', type=Path, default=Path('results/wide_binary_kinematics.json'))
    args = parser.parse_args()
    rows = load_pairs(args.input)
    results = []
    for i, row in enumerate(rows):
        try:
            base = projected_kinematics(row)
            results.append({'pair_id': row['pair_id'], **base, **chi2_components(row),
                            'speed_sigma_rho0_kms': delta_method_speed_sigma(row),
                            'speed_sigma_rho05_kms': delta_method_speed_sigma(row, .5),
                            'mass_prior_mc': monte_carlo_speed_ratio(
                                row, mass_fractional_sigma=.2, draws=3000, seed=20261101 + i)})
        except ValueError as exc:
            results.append({'pair_id': row['pair_id'], 'excluded_reason': str(exc)})
    valid = [r for r in results if 'excluded_reason' not in r]
    payload = {
        'data_kind': 'retained_Gaia_DR3_double_white_dwarf_pairs',
        'input': str(args.input), 'n_input': len(rows), 'n_valid': len(valid),
        'assumptions': {'total_mass_msun': 1.2, 'mass_lognormal_sigma': .2,
                        'hypothetical_pm_component_rho': [0, .5],
                        'independent_parallax_pm_errors': True,
                        'radial_velocity_available': False},
        'median_projected_separation_au': float(np.median([r['separation_au'] for r in valid])) if valid else None,
        'median_relative_speed_kms': float(np.median([r['relative_speed_kms'] for r in valid])) if valid else None,
        'pairs': results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2), encoding='utf-8')
    print(json.dumps({'n_input': len(rows), 'n_valid': len(valid),
                      'median_relative_speed_kms': payload['median_relative_speed_kms']}))


if __name__ == '__main__':
    main()

# Local Completion Report — Gaia Wide-Binary Astrometric Consistency Audit

Author: Biswajit Jana. This report documents a local Claude Code implementation pass
(project 7 of the 30-project pack, `BUILD_FIRST` priority 9.1/10). No git operations
were performed. Nothing has been published.

## 1. Environment

- New dedicated conda env `gaia-wide-binary-consistency-audit` (Python 3.11),
  pinned to this project's own `pyproject.toml`: numpy==1.26.4, scipy==1.13.1,
  pandas==2.2.2, matplotlib==3.9.0, pyyaml==6.0.1, astropy==6.1.0,
  astroquery==0.4.7, requests==2.32.3; dev: pytest==8.2.2, pytest-cov==5.0.0,
  ruff==0.5.5, mypy==1.10.1, types-PyYAML, types-requests.
- No local LaTeX toolchain (same limitation as sibling projects).

## 2. Files created or changed

Foundation (`config.py`, `exceptions.py`, `logging_utils.py`, `provenance.py`,
`results_io.py`), data layer (`scripts/fetch_data.py`, `synthetic.py`,
`scripts/sync_web_assets.py` — new this session), scientific modules (`io.py`,
`quality.py`, `residuals.py`, `statistics.py`, `uncertainty.py`, `benchmarks.py`,
`plotting.py`, `core.py`), 12 test files (60 tests), figures/report
(`scripts/make_figures.py`, `reports/report.tex`, `reports/references.bib` — both
rewritten this session with real numbers), and the web dashboard
(`web-react/src/App.jsx` rewritten, `eslint.config.js` fixed, `recharts` removed,
`public/project.json` rewritten — all this session).

## 3. Exact commands run (in order)

```bash
python -m pip install -e ".[dev]"
pytest -q                                  # 60 passed
ruff check src tests scripts               # All checks passed
mypy src                                   # Success: no issues found in 15 source files
python scripts/run_analysis.py --demo
python scripts/make_figures.py --demo
# Real-data pipeline, run only after explicit operator authorization in chat:
python scripts/fetch_data.py --i-have-authorization --n-pairs 30
python scripts/run_analysis.py --real
python scripts/make_figures.py --real
python scripts/sync_web_assets.py
cd web-react && npm install && npm run lint && npm run build
```

## 4. Test / lint / build results

- **pytest**: 60 tests passed, 0 failed.
- **ruff**: clean on `src tests scripts`.
- **mypy**: clean on `src` (0 errors, 15 source files).
- **web-react**: `npm run lint` and `npm run build` both clean after applying the
  established `eslint.config.js` `react/jsx-uses-vars` fix and `recharts` removal.

### Bugs found and fixed during implementation

1. **Real bug, found only against the live archive**: the originally-planned
   VizieR catalogue designation for El-Badry, Rix & Heintz (2021),
   `J/MNRAS/506/2269`, does not actually exist in VizieR's TAP_SCHEMA — a prior
   IMPLEMENTATION_PLAN.md draft had incorrectly claimed this was "live-verified"
   when it had not actually been tested against the archive. Diagnosed by a
   direct TAP `TAP_SCHEMA.tables` query against `tapvizier.cds.unistra.fr`
   returning zero rows for that table name (and confirmed via
   `astroquery.vizier.Vizier.get_catalogs()` on two mirrors). Fixed by
   substituting a real, live-verified, directly relevant alternative: VizieR
   `J/ApJ/934/148/tablea1` (Heintz, Hermes, El-Badry et al., Wide White Dwarf
   Binary Catalog) — same underlying consistency question, narrower population.
   `io.py`, `fetch_data.py`, `IMPLEMENTATION_PLAN.md`, `report.tex`, and
   `references.bib` were all updated to document this substitution honestly
   rather than silently swap the citation.
2. Standard `_masked_scalar()` NULL-handling pattern (from
   euclid-q1-vis-psf-astrometry-audit) reused for Gaia DR3 cross-match NULL
   fields.

## 5. Real datasets accessed

`astroquery.vizier.Vizier` for the wide-binary candidate list, `astroquery.gaia.Gaia`
for authoritative DR3 astrometry per component (same pattern verified in project 2).

- **Catalogue query**: VizieR `J/ApJ/934/148/tablea1`, 30 deterministic candidate
  pairs (row-limited query, not random).
- **Gaia DR3 cross-match**: all 60 unique component `source_id` values
  successfully cross-matched against `gaiadr3.gaia_source` (0 skipped for
  incomplete astrometry).
- **Licence/terms**: CDS Strasbourg (VizieR catalogue terms) and ESA Gaia
  archive data access rights.
- Full SHA-256 and provenance in `data/manifest.csv`; per-pair astrometry in
  `data/processed/real_pairs.csv`; per-pair separation/chance-alignment in
  `data/source_catalog.csv`. Raw query results are not committed.

## 6. Validation and uncertainty outcomes

- **Synthetic scale-recovery gate**: PASSED. 6 injected true scale factors
  (0.5–4.0) all recovered exactly on the 1:1 line.
- **Component-swap invariance**: confirmed — swapping component 1/2 labels
  leaves z² and χ²_pm unchanged.
- **Failure-mode tests**: missing/malformed pair records, non-finite input,
  too-few-points — all raise the documented exceptions.
- **Real-data result**: 40% of 30 real pairs flagged inconsistent at the
  configured threshold. Empirical uncertainty scale factor S=9.08 for the
  full "good"-quality sample (n=30); by magnitude S=3.24 (G>18, n=27) to
  S=27.0 (15<G≤18, n=3, very noisy); by separation S ranges 1.03–13.9 across
  4 sub-bins (n=3–12 each). The normalized-residual histogram shows a real
  outlier tail out to |z|≈70. **Genuine finding, not fabricated**: large
  scale factors are plausibly driven by real orbital motion in physically
  close white-dwarf pairs (the pipeline assumes zero true relative proper
  motion), not purely a Gaia uncertainty-calibration defect — documented
  explicitly in report.tex Limitations rather than overclaimed as a pure
  miscalibration finding.
- All magnitude and separation bins (n<30) are below
  `minimum_sample_size=30` and flagged, not hidden, in `results/warnings.json`.

## 7. Remaining TODOs / unresolved risks

- `reports/report.tex` could not be compiled to PDF locally (no LaTeX
  toolchain); structural completeness was checked, not a rendered PDF.
- Real-data sample is intentionally small (30 pairs) and drawn from a
  different, narrower catalogue than originally planned (white dwarf pairs,
  not the general El-Badry stellar sample) — a first-release scope
  substitution, not a general characterization of Gaia uncertainty
  calibration for all wide binaries.
- Orbital-motion confound in close pairs is identified but not corrected
  for (e.g. via a period cut); a natural next extension.
- Proper-motion correlation terms (pmra/pmdec covariance) are not retained
  from the archive columns used, a conservative simplification.

## 8. Claims safe for a public README

- "Implements a reproducible pipeline auditing whether Gaia DR3 component
  parallax/proper-motion measurements in wide-binary pairs are statistically
  consistent with their quoted uncertainties, validated against a synthetic
  scale-recovery gate before use on real data."
- "On a real sample of 30 wide double white dwarf pairs (VizieR
  J/ApJ/934/148, cross-matched against live Gaia DR3), 40% of pairs are
  flagged inconsistent, with empirical uncertainty scale factors above 1 in
  most bins — plausibly reflecting real orbital motion in close pairs rather
  than purely a Gaia calibration defect."
- "60 automated tests including a synthetic scale-recovery validation gate,
  a component-swap invariance test, and failure-mode tests; ruff- and
  mypy-clean."
- "A compact uncertainty-calibration audit; not a new binary catalogue,
  orbit fit, or gravity test."

## 9. Claims that must NOT be made

- Do not claim this characterizes Gaia's uncertainty calibration for wide
  binaries in general — the real sample is 30 white dwarf pairs from one
  catalogue, not the general stellar wide-binary population.
- Do not claim the large scale factors are proof of Gaia uncertainty
  miscalibration — orbital motion in close pairs is a real, undisentangled
  confound documented in Limitations.
- Do not claim the magnitude/separation-binned trends are statistically
  significant — every such bin is below the configured minimum sample size.
- Do not claim the TeX report PDF has been visually verified — only its
  source structure was checked.

## 10. Manual review checklist for Biswajit

- [ ] Compile `reports/report.tex` locally/Overleaf and read the PDF end-to-end.
- [ ] Decide whether to pursue a period-cut or joint-orbit-fit extension to
      separate genuine uncertainty miscalibration from orbital motion.
- [ ] Consider whether the catalogue substitution (white dwarf pairs instead
      of the general El-Badry stellar sample) should be reflected in the
      project title/scope, or whether a larger real sample from a different
      accessible catalogue should be pursued instead.
- [ ] Review `npm audit` output and decide whether to bump pinned frontend
      tooling.
- [ ] Follow `MANUAL_GITHUB_ONE_BY_ONE.md` for the actual repository creation
      and push — none of that was done in this session.

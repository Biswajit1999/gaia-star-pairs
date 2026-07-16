# Implementation Plan — Gaia Wide-Binary Astrometric Consistency Audit

Author: Biswajit Jana. Local implementation pass. No git/remote operations.

## 1. Literature verification (docs/LITERATURE_SEEDS.md)

Verified live via WebFetch against arXiv abstract pages / CrossRef API in this session:

1. **El-Badry, Rix & Heintz (2021)** — "A million binaries from Gaia eDR3: sample
   selection and validation of Gaia parallax uncertainties", MNRAS 506, 2269-2295.
   arXiv:2101.05282. DOI 10.1093/mnras/stab323 confirmed via `api.crossref.org`.
   VERIFIED.
2. **Public catalogue deposit** — Zenodo record, DOI 10.5281/zenodo.4435257,
   "Wide binaries from Gaia eDR3", K. El-Badry, CC-BY-4.0. Files:
   `all_columns_catalog.fits.gz` (1.4 GB), `all_columns_catalog_shift.fits.gz`
   (354.1 MB). VERIFIED (too large to download whole; see §2 access plan).
3. **Gaia DR3 official documentation** — Gaia Collaboration, Vallenari et al.
   (2023), "Gaia Data Release 3: Summary of the content and survey properties",
   A&A 674, A1. arXiv:2208.00211, DOI 10.1051/0004-6361/202243940. VERIFIED.
4. **El-Badry (2024)** — "Gaia's binary star renaissance", New Astronomy Reviews.
   arXiv:2403.12146. VERIFIED (DOI resolves via arXiv DOI 10.48550/arXiv.2403.12146;
   journal DOI not yet minted at verification time — noted in references.bib).
5. **Astropy core package paper** — The Astropy Collaboration, Price-Whelan et al.
   (2022), "The Astropy Project: Sustaining and Growing a Community-oriented
   Open-source Project and the Latest Major Release (v5.0) of the Core Package",
   ApJ 935, 167. arXiv:2206.14220, DOI 10.3847/1538-4357/ac7c74. VERIFIED.

## 2. Real-data access plan (verified live, not assumed)

**Correction (re-verified live in a later session)**: the originally-planned
VizieR designation `J/MNRAS/506/2269` for El-Badry, Rix & Heintz (2021) does
**not** actually exist in VizieR's TAP_SCHEMA — a direct TAP query against
`tapvizier.cds.unistra.fr` for `table_name LIKE '%MNRAS/506%'` and `%2269%`
returns no matching table, and `astroquery.vizier.Vizier.get_catalogs()`
returns zero tables for that ID on both the primary and Harvard mirrors. The
prior IMPLEMENTATION_PLAN.md claim that this was "live-verified" was
incorrect — it was not actually tested against the archive. The El-Badry et
al. (2021) million-binaries sample is only available as the full Zenodo
deposit (10.5281/zenodo.4435257, ~1.4 GB gzipped FITS), far larger than
appropriate for a first-release bounded audit per `docs/DATASET_PLAN.md`.

**Real, live-verified alternative used instead**: VizieR catalogue
`J/ApJ/934/148/tablea1` — Heintz, Hermes, El-Badry, Walsh, van Saders,
Fields & Koester, "The Wide White Dwarf Binary Catalog" (with a 2023
erratum, ApJ 934, 148; erratum 2023ApJ...952...92H). Confirmed live via
`astroquery.vizier.Vizier(row_limit=...).get_catalogs('J/ApJ/934/148/tablea1')`
returning real rows with columns `GaiaPrim`/`GaiaSec` (component Gaia DR3
source_ids), `Sep` (AU), `Chance` (chance-alignment probability), plus
per-component `plx`/`e_plx`/`pmRA`/`e_pmRA`/`pmDE`/`e_pmDE`/`Gmag` already in
the table. This is a real, citable, directly relevant wide-binary Gaia
astrometry catalogue for the same co-moving-pair consistency question (wide
double white dwarf pairs rather than the general stellar sample) — same
underlying physics (component parallax/PM consistency test), narrower
population, documented as a scope note in Limitations.

Pipeline: (a) query VizieR `J/ApJ/934/148/tablea1` for a deterministic,
row-limited sample of wide-binary pairs (GaiaPrim, GaiaSec, Sep, Chance);
(b) cross-match every component Gaia source_id against a live
`astroquery.gaia.Gaia` DR3 TAP query (`gaiadr3.gaia_source`, `SOURCE_ID IN (...)`)
for authoritative parallax/pm astrometry, uncertainties, and RUWE (not
present in the VizieR table) used in the consistency statistics. This
matches the pattern in `euclid-q1-vis-psf-astrometry-audit/src/.../gaia_match.py`
(case-insensitive column lookup — Gaia TAP returns `SOURCE_ID` uppercase
regardless of query casing) and avoids ever downloading the multi-hundred-MB
Zenodo files.

## 3. Module map (docs/RESEARCH_BLUEPRINT.md + established foundation pattern)

Foundation (ported near-verbatim from sibling projects, renamed package):
`config.py`, `exceptions.py` (extended), `logging_utils.py`, `provenance.py`
(extended), `results_io.py`, `synthetic.py`.

Domain modules (docs/RESEARCH_BLUEPRINT.md's "Reusable scientific modules"):
- `io.py` — load the source_catalog.csv of paired components; live VizieR +
  Gaia DR3 query helpers (network-touching, shared by fetch_data.py and any
  script needing a fresh pull).
- `quality.py` — RUWE / binary-probability strict-vs-permissive quality cuts.
- `residuals.py` — per-pair normalized parallax residual (z) and proper-motion
  chi-square (2 dof), plus component-swap invariance helper.
- `statistics.py` — magnitude/separation/quality binning of the consistency
  statistic and the uncertainty "scale factor" (sqrt(mean(z^2))) per bin.
- `uncertainty.py` — `bootstrap_statistic` (observational) and
  `check_fit_convergence` (numerical), kept separate per docs/VALIDATION_CONTRACT.md.
- `benchmarks.py` — tracemalloc + perf_counter wrapper, JSON writer.
- `plotting.py` — kept as the smoke-test demo plot helper (pre-existing).
- `core.py` — `run_pipeline` orchestrator; per-pair try/except over
  InsufficientDataError/ConvergenceError/DataSchemaError -> warning, never abort.

## 4. Scientific design

For each wide-binary pair with quoted Gaia parallax (plx, sigma_plx) and proper
motion (pmra, sigma_pmra, pmdec, sigma_pmdec) per component:

- `z_parallax = (plx1 - plx2) / sqrt(sigma_plx1^2 + sigma_plx2^2)`
- `chi2_pm = ((pmra1-pmra2)/sqrt(sigma_pmra1^2+sigma_pmra2^2))^2 + ((pmdec1-pmdec2)/sqrt(sigma_pmdec1^2+sigma_pmdec2^2))^2`
  (2 dof; pmra/pmdec correlation terms are not available from the archive
  columns retained here and are explicitly documented as a limitation —
  ignoring them is conservative in the sense of not hiding excess scatter).

If Gaia's quoted uncertainties are correctly calibrated and the pair is a
genuine common-distance, co-moving system, `z_parallax` should be
~N(0,1)-distributed and `chi2_pm` ~chi2(2)-distributed. The **uncertainty scale
factor** `S = sqrt(mean(z^2))` per bin (magnitude / separation / quality) is the
primary reported metric: `S ~= 1` means quoted uncertainties are well
calibrated; `S > 1` means Gaia understates the true scatter in that bin. This
directly answers the bounded scientific question.

## 5. Validation contract mapping

- **synthetic scale recovery**: `synthetic.py` generates pairs with a known
  injected scale factor S_true (residuals drawn as `S_true * N(0,1) * sigma`);
  pipeline must recover S_true within tolerance — implemented as a pytest gate
  that must pass before real data is used.
- **component-swap invariance**: swapping component 1/2 labels must leave
  `z_parallax^2` and `chi2_pm` unchanged (sign of z flips, square doesn't).
- **bootstrap bin scales**: `uncertainty.bootstrap_statistic` over per-bin z^2.
- **quality-cut sensitivity**: `quality.py` strict vs permissive RUWE/binary-
  probability cuts, scale factor reported under both.
- **runtime/memory**: `benchmarks.py` + `scripts/run_analysis.py`.

## 6. Files to write (in order)

1. `src/.../exceptions.py` (extend), `config.py` (new), `logging_utils.py` (new)
2. `src/.../provenance.py` (extend to full pattern), `results_io.py` (new)
3. `src/.../synthetic.py` (new)
4. `src/.../io.py`, `quality.py`, `residuals.py`, `statistics.py`,
   `uncertainty.py`, `benchmarks.py`, `core.py`
5. `tests/` — one file per module + injection-recovery + null-control +
   failure-mode tests + `conftest.py` fixtures
6. `scripts/fetch_data.py`, `scripts/run_analysis.py`, `scripts/make_figures.py`,
   `scripts/sync_web_assets.py`
7. `reports/report.tex`, `reports/references.bib`
8. `web-react/eslint.config.js` fix, `package.json` (drop recharts),
   `src/App.jsx`, `public/project.json`
9. `LOCAL_COMPLETION_REPORT.md`, `_PROJECT_LOG.md`

## 7. Stop conditions checked

None triggered at planning time. VizieR live-query access will be re-verified
programmatically in `scripts/fetch_data.py` before any real-data run; if it
fails, the script raises `ArchiveAccessError` and the run stops rather than
falling back to fabricated data.

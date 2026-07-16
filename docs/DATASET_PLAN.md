# Dataset Plan

## Mode

**real public wide-binary catalogue**

## Official sources and literature seeds

- El-Badry, Rix & Heintz 2021, DOI:10.1093/mnras/stab323, arXiv:2101.05282
- Public catalogue deposit/Zenodo
- Gaia DR3 official documentation
- El-Badry 2024 binary-star review, arXiv:2403.12146
- Astropy core package paper

## Acquisition rules

- Prefer official mission/archive endpoints and author-maintained catalogue deposits.
- Record product identifier, query, retrieval UTC, source URL, file size, checksum and licence/terms.
- Do not commit large raw FITS, HDF5 or catalogue files.
- Store a deterministic manifest under `data/manifest.csv`.
- Store only a tiny, clearly labelled synthetic/example dataset in `data/example/`.
- Never replace inaccessible real data with fabricated values while presenting them as observations.

## Required manifest columns

`product_id, source, source_url, retrieved_utc, sha256, file_size_bytes, selection_reason, licence_or_terms`

## FAIR contract

Every derived product must point to the raw product ID, software commit, configuration hash and transformation script.

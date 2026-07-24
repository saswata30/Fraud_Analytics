# Sample raw data

Pre-generated synthetic raw files for the workshop — the same data `notebooks/02_generate_data.py`
produces (seed 42). They let you skip the generation step and load Bronze directly, and they mirror
what lands in the `raw/input` volume.

| File | Grain | Rows | Notes |
|------|-------|------|-------|
| `claims.csv` / `claims.parquet` | one row per claim | 5,020 | Carries the `is_fraud` label; includes intentional data-quality issues (nulls, negatives, whitespace, duplicates) for the Silver cleaning step. |
| `policyholders.csv` / `policyholders.parquet` | one row per customer | 1,500 | Customer dimension (region, tenure, credit score, demographics). |

> These are regenerated deterministically by notebook `02`. To reproduce, run that notebook — it
> writes the same files to `/Volumes/<catalog>/<schema>/raw/input`. Uploaded user documents land in
> `raw/input/userdata` (see `docs/`).

# Fraud Analytics — Insurance Workshop

An end-to-end Databricks workshop for **insurance fraud analytics**, built for Vocarium Labs.
Clone it into any Databricks workspace and run the notebooks in order. It walks from raw synthetic
data all the way to a Genie Space and a chat app.

## What you'll build

```
Raw files (CSV/Parquet)  →  Bronze  →  Silver  →  Gold  →  Genie Space  →  Chat App
     (volume)              (Delta)   (cleaned)  (enriched)   (NL Q&A)     (Databricks App)
```

## Notebooks (run in order)

| # | Notebook | What it does |
|---|----------|--------------|
| 01 | `notebooks/01_setup.py` | Creates catalog `allianz_workshop` (falls back to `default`), schema `fraud_analytics`, and volume `raw/input` (plus `raw/input/userdata` for app uploads). |
| 02 | `notebooks/02_generate_data.py` | Generates 5,000+ synthetic insurance claims + 1,500 policyholders (with a learnable fraud signal) as CSV and Parquet. |
| 03 | `notebooks/03_load_to_bronze.py` | Loads the raw files into Bronze Delta tables with audit columns. |
| 04 | `notebooks/04_prompt_for_visual_data_prep.py` | Prompt playbook for **Visual Data Prep** to build Bronze→Silver→Gold with data-quality checks, published as a Lakeflow job. |
| 05 | `notebooks/05_genie_space_setup.py` | Step-by-step: create, instruct, **benchmark**, and **monitor** a Genie Space over the Gold tables. |
| 06 | `notebooks/06_prompt_for_chat_app.py` | Design brief + prompt playbook (for **Genie Code**) for the Databricks App. |

## The app

The [`app/`](app/) folder is a **working React + FastAPI Databricks App** — a clean, light
"insights" dashboard (navy rail, blue accent, SVG charts) with two screens:

- **Overview** — fraud-rate KPIs, fraud-over-time, fraud by region/policy, risk-score distribution, high-risk claims table.
- **Ask Genie** — natural-language chat over the fraud data via the Genie Conversation API, plus
  document upload. **Uploaded files land in `raw/input/userdata`.**

Deploy it directly (see [`app/README.md`](app/README.md)) or regenerate it with Genie Code using notebook `06`.

## Sample documents (`docs/`)

Upload these in the **Ask Genie** panel, then ask grounded questions:

- [`docs/sample_fraud_event_report.md`](docs/sample_fraud_event_report.md) — a verbose SIU fraud investigation tied to the dataset.
- [`docs/sample_eu_compliance_policy.md`](docs/sample_eu_compliance_policy.md) — an EU/GDPR compliance framework for fraud analytics.
- [`docs/genie_sample_questions.md`](docs/genie_sample_questions.md) — 10+ ready-to-use Genie questions (data + document-grounded).

## Quick start

1. In Databricks: **Workspace → Repos → Add Repo** and paste this repo's Git URL.
2. Open `notebooks/01_setup.py`, attach Serverless (or a cluster), **Run all**.
3. Run `02` and `03` the same way.
4. Follow `04`, `05`, `06` — these are guided playbooks you run inside Visual Data Prep, Genie, and Genie Code.

> **Naming:** everything defaults to catalog `allianz_workshop` / schema `fraud_analytics`. If your workspace
> can't create catalogs, notebook `01` automatically falls back to the `default` catalog — just set
> `CATALOG = "default"` at the top of notebooks `02`–`04` to match.

## Dataset

- **`claims`** (5,000+ rows) — one row per insurance claim; carries the `is_fraud` label plus amounts,
  channels, reporting lag, and prior-claim counts. Intentionally seeded with data-quality issues
  (nulls, negatives, whitespace, duplicates) so the Silver cleaning step has real work to do.
- **`policyholders`** (1,500 rows) — customer dimension (region, tenure, credit score, demographics).

Fraud is ~7% of claims and correlates with higher payouts, faster reporting, newer customers, and
lower credit scores — so it's learnable in Genie and downstream ML.

## Screenshots

_Add your own screenshots here._

## License

See [LICENSE](LICENSE).

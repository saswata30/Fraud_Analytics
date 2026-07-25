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

**Setup notebooks 01–03 are pure SQL** and run on a **Serverless SQL Warehouse** — no all-purpose
cluster required (most workshop labs only provide a SQL Warehouse). Notebooks 04–07 are prompt
playbooks. Attach each to the SQL Warehouse and **Run all**, in order.

| # | Notebook | What it does |
|---|----------|--------------|
| 01 | `notebooks/01_setup.sql` | Creates catalog `allianz_lab` and schema `fraud_analytics`. |
| 02 | `notebooks/02_generate_data.sql` | Generates 5,000 claims + 1,500 policyholders (with a learnable fraud signal) as raw tables — pure SQL. |
| 03 | `notebooks/03_load_to_bronze.sql` | Builds Bronze → Silver → Gold, incl. `gold_fraud_claims` / `gold_fraud_by_region`. |
| 04 | `notebooks/04_prompt_for_visual_data_prep.py` | Prompt playbook for **Visual Data Prep** (Bronze→Silver→Gold + data-quality checks). |
| 05 | `notebooks/05_genie_space_setup.py` | Step-by-step: create, instruct, **benchmark**, **monitor** a Genie Space over the Gold tables. |
| 06 | `notebooks/06_create_dashboard.py` | Prompt playbook to build an **AI/BI (Lakeview) dashboard** over the Gold tables. |
| 07 | `notebooks/07_prompt_for_chat_app_optional.py` | *(optional)* Deploy the ready-made Databricks **App** from `app/` (reuse, don't rebuild). |

> Everything downstream (Genie, the app, Visual Data Prep) runs on the SQL Warehouse too — no
> cluster needed anywhere. The earlier Python/Spark versions of 01–03 are preserved in git history
> if your workspace has an all-purpose cluster.

## The app

The [`app/`](app/) folder is a **working React + FastAPI Databricks App** — a clean, light
"insights" dashboard (navy rail, blue accent, SVG charts) with two screens:

- **Overview** — fraud-rate KPIs, fraud-over-time, fraud by region/policy, risk-score distribution, high-risk claims table.
- **Ask Genie** — natural-language chat over the fraud data via the Genie Conversation API, plus
  document upload. **Uploaded files land in `raw/input/userdata`.**

Deploy it directly (see [`app/README.md`](app/README.md) or notebook `07`) or regenerate it with Genie Code using notebook `07`.

## Documents (`docs/`)

Upload the PDFs in the **Ask Genie** panel (they land in `raw/input/userdata`), then ask grounded questions:

- [`docs/fraud_event_report.pdf`](docs/fraud_event_report.pdf) — a realistic SIU fraud investigation report (letterhead, exhibits, sign-off), tied to the dataset fields.
- [`docs/eu_compliance_policy.pdf`](docs/eu_compliance_policy.pdf) — an EU/GDPR + AI Act compliance framework for fraud analytics.
- [`docs/genie_questions.docx`](docs/genie_questions.docx) — 20+ ready-to-use Genie questions (data + document-grounded).
- [`docs/build_docs.py`](docs/build_docs.py) — regenerates the PDFs/DOCX (`pip install reportlab python-docx`).

## Quick start

1. In Databricks: **Workspace → Repos → Add Repo** and paste this repo's Git URL.
2. Open `notebooks/01_setup.py`, attach Serverless (or a cluster), **Run all**.
3. Run `02` and `03` the same way.
4. Follow `04`, `05`, `06`, and (optionally) `07` — guided playbooks for Visual Data Prep, Genie, the AI/BI dashboard, and deploying the app.

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

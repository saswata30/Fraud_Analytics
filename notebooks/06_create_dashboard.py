# Databricks notebook source
# MAGIC %md
# MAGIC # 06 · Create a Dashboard — AI/BI (Lakeview) over the Gold tables
# MAGIC
# MAGIC This notebook is a **prompt playbook + step-by-step guide** to build a **Databricks AI/BI
# MAGIC (Lakeview) dashboard** on top of the fraud analytics **Gold tables**. There is no code to run —
# MAGIC paste the prompts into the **dashboard's Assistant** (the ✨ icon), or follow the manual steps.
# MAGIC
# MAGIC The dashboard is the "at a glance" companion to the Genie Space (notebook `05`) and the app
# MAGIC (notebook `07`): all three read the **same** Gold tables.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Prerequisites
# MAGIC - Gold tables exist (from notebook `03` / Visual Data Prep in `04`):
# MAGIC   - **`gold_fraud_claims`** — one row per claim, enriched with risk flags + `fraud_risk_score` (0–4).
# MAGIC   - **`gold_fraud_by_region`** — fraud aggregates by `region` × `policy_type`.
# MAGIC - A running **Serverless SQL Warehouse** and `SELECT` on the tables.
# MAGIC - **Catalog note:** notebooks `01`–`03` create the tables as **`<default_catalog>.fraud_analytics`**
# MAGIC   (the warehouse's default catalog — run `SELECT current_catalog()` to confirm). Substitute that
# MAGIC   catalog name wherever you see `<catalog>` below.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 1 · Create the dashboard
# MAGIC In the left sidebar choose **Dashboards → Create dashboard**. Name it
# MAGIC **`Fraud Analytics — Overview`**. On the **Data** tab, add these two datasets (SQL):
# MAGIC
# MAGIC ```sql
# MAGIC -- Dataset: claims  (from gold_fraud_claims)
# MAGIC SELECT * FROM <catalog>.fraud_analytics.gold_fraud_claims;
# MAGIC ```
# MAGIC
# MAGIC ```sql
# MAGIC -- Dataset: by_region  (from gold_fraud_by_region)
# MAGIC SELECT * FROM <catalog>.fraud_analytics.gold_fraud_by_region;
# MAGIC ```

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 2 · Let the Assistant build it (paste this prompt)
# MAGIC Open the dashboard **Assistant** (✨) and paste the brief below. It describes every widget so
# MAGIC the generated layout matches the app's "Overview" screen.
# MAGIC
# MAGIC ```
# MAGIC Build a fraud analytics overview dashboard from the `claims` dataset
# MAGIC (gold_fraud_claims) and the `by_region` dataset (gold_fraud_by_region).
# MAGIC
# MAGIC Top row — 4 KPI counters:
# MAGIC   - Fraud Rate  = avg(is_fraud), formatted as a percentage
# MAGIC   - Total Claims = count(*)
# MAGIC   - Flagged Payout = sum(claim_amount) where is_fraud = 1, formatted as GBP (£)
# MAGIC   - High-Risk Claims = count(*) where fraud_risk_score >= 3
# MAGIC
# MAGIC Second row:
# MAGIC   - Line chart: fraud rate over time. X = claim_month, Y = avg(is_fraud). Red line.
# MAGIC   - Donut: fraud vs legitimate share of claims (count by is_fraud).
# MAGIC
# MAGIC Third row:
# MAGIC   - Horizontal bar: fraud rate by region (from by_region: sum(fraud_claims)/sum(total_claims)),
# MAGIC     sorted descending.
# MAGIC   - Horizontal bar: fraud rate by policy_type, sorted descending.
# MAGIC   - Bar/column: fraud_risk_score distribution (0–4), broken down by is_fraud (fraud red, legit grey).
# MAGIC
# MAGIC Bottom:
# MAGIC   - Table "Highest-Risk Claims": claim_id, region, policy_type, channel, claim_amount (GBP),
# MAGIC     fraud_risk_score, is_fraud. Sort by fraud_risk_score desc, limit 25.
# MAGIC
# MAGIC Add a top filter on `region` and `policy_type` that applies to all widgets.
# MAGIC Use a clean light theme; format money as GBP and rates as percentages.
# MAGIC ```

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 3 · Reference SQL for the key widgets
# MAGIC If you'd rather add widgets by hand (or check the Assistant's output), these queries back each tile.
# MAGIC
# MAGIC ```sql
# MAGIC -- KPI: fraud rate, total claims, flagged payout, high-risk count, avg claim
# MAGIC SELECT
# MAGIC   count(*)                                                  AS total_claims,
# MAGIC   round(avg(is_fraud), 4)                                   AS fraud_rate,
# MAGIC   sum(CASE WHEN is_fraud = 1 THEN claim_amount END)         AS flagged_payout,
# MAGIC   sum(CASE WHEN fraud_risk_score >= 3 THEN 1 ELSE 0 END)    AS high_risk_claims,
# MAGIC   round(avg(claim_amount), 2)                               AS avg_claim
# MAGIC FROM <catalog>.fraud_analytics.gold_fraud_claims;
# MAGIC ```
# MAGIC
# MAGIC ```sql
# MAGIC -- Line: fraud rate over time
# MAGIC SELECT claim_month, round(avg(is_fraud), 4) AS fraud_rate, count(*) AS claims
# MAGIC FROM <catalog>.fraud_analytics.gold_fraud_claims
# MAGIC GROUP BY claim_month ORDER BY claim_month;
# MAGIC ```
# MAGIC
# MAGIC ```sql
# MAGIC -- Bars: fraud rate by region (uses the pre-aggregated gold table)
# MAGIC SELECT region,
# MAGIC        sum(fraud_claims) / sum(total_claims) AS fraud_rate,
# MAGIC        sum(total_claims)                     AS claims
# MAGIC FROM <catalog>.fraud_analytics.gold_fraud_by_region
# MAGIC GROUP BY region ORDER BY fraud_rate DESC;
# MAGIC ```
# MAGIC
# MAGIC ```sql
# MAGIC -- Column: fraud_risk_score distribution, split fraud vs legit
# MAGIC SELECT fraud_risk_score,
# MAGIC        sum(CASE WHEN is_fraud = 1 THEN 1 ELSE 0 END) AS fraud,
# MAGIC        sum(CASE WHEN is_fraud = 0 THEN 1 ELSE 0 END) AS legit
# MAGIC FROM <catalog>.fraud_analytics.gold_fraud_claims
# MAGIC GROUP BY fraud_risk_score ORDER BY fraud_risk_score;
# MAGIC ```
# MAGIC
# MAGIC ```sql
# MAGIC -- Table: highest-risk claims
# MAGIC SELECT claim_id, region, policy_type, channel, claim_amount, fraud_risk_score, is_fraud
# MAGIC FROM <catalog>.fraud_analytics.gold_fraud_claims
# MAGIC ORDER BY fraud_risk_score DESC, claim_amount DESC
# MAGIC LIMIT 25;
# MAGIC ```

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 4 · Publish & share
# MAGIC - Click **Publish** so viewers see the latest data. Pick **"run as owner"** (or a service
# MAGIC   principal with `SELECT`) so viewers don't each need table grants.
# MAGIC - **Share** with your workshop audience. Optionally set a **refresh schedule** on the datasets.
# MAGIC - Add a **"Open in Genie"** link (or embed the Genie Space from notebook `05`) so users can drill
# MAGIC   from a chart into a natural-language follow-up.

# COMMAND ----------

# MAGIC %md
# MAGIC ### ✅ Dashboard complete
# MAGIC You now have the three consumption surfaces over the **same Gold tables**:
# MAGIC **Dashboard** (this notebook) · **Genie Space** (`05`) · **App** (`07`, optional).
# MAGIC Next: deploy the ready-made app in **`07_prompt_for_chat_app_optional`**.

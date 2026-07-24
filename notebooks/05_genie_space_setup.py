# Databricks notebook source
# MAGIC %md
# MAGIC # 05 · Create a Genie Space — Step by Step
# MAGIC
# MAGIC **Databricks Genie** lets business users ask natural-language questions of the Gold tables and get back
# MAGIC SQL, tables, and charts. This notebook is a **step-by-step guide** to create, instruct, benchmark, and
# MAGIC monitor a Genie Space for the fraud analytics dataset.
# MAGIC
# MAGIC > Genie Spaces are created in the Databricks UI (**Genie** in the left sidebar). This notebook is the
# MAGIC > playbook; there is no code to run except the optional verification queries at the end.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 1 · Prerequisites
# MAGIC - The Gold tables from notebook `04` exist: `gold_fraud_claims`, `gold_fraud_by_region`.
# MAGIC - You have a running **SQL Warehouse** (Serverless recommended).
# MAGIC - You have `CAN USE` on the warehouse and `SELECT` on the tables.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 2 · Create the Genie Space
# MAGIC 1. In the left sidebar, click **Genie**.
# MAGIC 2. Click **New** (top right) → **New Genie Space**.
# MAGIC 3. **Title:** `Insurance Fraud Analytics`.
# MAGIC 4. **Description:** `Ask questions about insurance claims and fraud patterns for the Allianz workshop.`
# MAGIC 5. **Default warehouse:** select your Serverless SQL Warehouse.
# MAGIC 6. **Tables:** add
# MAGIC    - `allianz_workshop.fraud_analytics.gold_fraud_claims`
# MAGIC    - `allianz_workshop.fraud_analytics.gold_fraud_by_region`
# MAGIC 7. Click **Save**.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 3 · Add General Instructions
# MAGIC In the Genie Space, open **Instructions → General instructions** and paste:
# MAGIC
# MAGIC ```
# MAGIC This space answers questions about insurance claims and fraud for an insurer.
# MAGIC - `is_fraud` = 1 means a confirmed fraudulent claim, 0 means legitimate.
# MAGIC - "Fraud rate" = SUM(is_fraud) / COUNT(*) unless the user says otherwise.
# MAGIC - Monetary amounts are in GBP; format them with a £ prefix and thousands separators.
# MAGIC - `fraud_risk_score` ranges 0-4; higher means more risk indicators present.
# MAGIC - When users ask about "risky" claims, filter fraud_risk_score >= 3.
# MAGIC - Always show the region or policy_type breakdown when the user asks "where" or "which".
# MAGIC - Prefer gold_fraud_by_region for aggregate/trend questions and gold_fraud_claims for row-level detail.
# MAGIC ```

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 4 · Add example SQL queries (few-shot)
# MAGIC Under **Instructions → SQL queries / Example queries**, add a few trusted examples so Genie learns the joins
# MAGIC and metrics. Add each with a natural-language title:
# MAGIC
# MAGIC **"What is the overall fraud rate?"**
# MAGIC ```sql
# MAGIC SELECT SUM(is_fraud) / COUNT(*) AS fraud_rate
# MAGIC FROM allianz_workshop.fraud_analytics.gold_fraud_claims;
# MAGIC ```
# MAGIC
# MAGIC **"Which regions have the highest fraud rate?"**
# MAGIC ```sql
# MAGIC SELECT region, SUM(is_fraud)/COUNT(*) AS fraud_rate, COUNT(*) AS claims
# MAGIC FROM allianz_workshop.fraud_analytics.gold_fraud_claims
# MAGIC GROUP BY region ORDER BY fraud_rate DESC;
# MAGIC ```
# MAGIC
# MAGIC **"Show total fraudulent payout by policy type"**
# MAGIC ```sql
# MAGIC SELECT policy_type, SUM(claim_amount) AS fraud_payout
# MAGIC FROM allianz_workshop.fraud_analytics.gold_fraud_claims
# MAGIC WHERE is_fraud = 1
# MAGIC GROUP BY policy_type ORDER BY fraud_payout DESC;
# MAGIC ```

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 5 · Add column descriptions / synonyms
# MAGIC Under **Instructions → Table & column annotations**, document the key columns and add synonyms so business
# MAGIC language maps to columns:
# MAGIC
# MAGIC | Column | Description | Synonyms |
# MAGIC |--------|-------------|----------|
# MAGIC | `is_fraud` | 1 = fraudulent claim, 0 = legitimate | fraudulent, fraud flag |
# MAGIC | `claim_amount` | Claim payout in GBP | payout, value, amount |
# MAGIC | `fraud_risk_score` | 0-4 count of risk indicators | risk score, risk level |
# MAGIC | `report_lag_days` | Days between incident and report | reporting delay |
# MAGIC | `policy_type` | Auto/Home/Health/Travel/Life/Commercial | product, line of business |

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 6 · Benchmark the Genie Space
# MAGIC Databricks Genie has a built-in **Benchmarks** tab to measure answer accuracy against a curated question set.
# MAGIC
# MAGIC 1. In the Genie Space, open the **Benchmarks** tab.
# MAGIC 2. Click **Add benchmark question**.
# MAGIC 3. For each question, provide the **expected SQL** (the ground truth). Suggested starter set:
# MAGIC
# MAGIC | # | Question | Expected answer checks |
# MAGIC |---|----------|------------------------|
# MAGIC | 1 | What is the overall fraud rate? | single value ≈ 0.07 |
# MAGIC | 2 | Which region has the most fraud? | returns a region + count |
# MAGIC | 3 | Total fraudulent payout for Auto policies? | sum of claim_amount where is_fraud=1, policy_type='Auto' |
# MAGIC | 4 | How many high-value fraudulent claims? | count where high_value_flag and is_fraud=1 |
# MAGIC | 5 | Average risk score for fraud vs non-fraud? | two averages, fraud higher |
# MAGIC
# MAGIC 4. Click **Run benchmark**. Genie generates SQL for each question and compares result sets to your expected SQL.
# MAGIC 5. Review the **accuracy score**. For any failures, refine General Instructions or add an example query, then re-run.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 7 · Monitor usage
# MAGIC 1. **Genie → Monitoring tab:** view question volume, thumbs-up/down feedback, and low-confidence answers.
# MAGIC 2. Triage 👎 answers weekly — each is a candidate for a new example query or instruction.
# MAGIC 3. **System tables** for deeper analysis (query history over the space's warehouse):
# MAGIC
# MAGIC ```sql
# MAGIC SELECT statement_text, executed_by, total_duration_ms, execution_status, start_time
# MAGIC FROM system.query.history
# MAGIC WHERE start_time >= current_date() - INTERVAL 7 DAYS
# MAGIC ORDER BY start_time DESC
# MAGIC LIMIT 100;
# MAGIC ```

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 8 · (Optional) Verify the tables are Genie-ready
# MAGIC Run these to confirm the Gold tables answer the benchmark questions before you wire up Genie.

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT SUM(is_fraud)/COUNT(*) AS overall_fraud_rate
# MAGIC FROM allianz_workshop.fraud_analytics.gold_fraud_claims;

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT region, SUM(is_fraud) AS fraud_claims, SUM(is_fraud)/COUNT(*) AS fraud_rate
# MAGIC FROM allianz_workshop.fraud_analytics.gold_fraud_claims
# MAGIC GROUP BY region ORDER BY fraud_rate DESC;

# COMMAND ----------

# MAGIC %md
# MAGIC ### ✅ Genie Space live
# MAGIC Next: open **`06_prompt_for_chat_app`** to build a chat + document-Q&A App on top of Genie.

-- Databricks notebook source
-- MAGIC %md
-- MAGIC # 03 · Bronze → Silver → Gold (SQL-only)
-- MAGIC
-- MAGIC Builds the Medallion tables from the raw tables created in `02`, in **pure SQL** on the
-- MAGIC **SQL Warehouse**:
-- MAGIC
-- MAGIC - **Bronze** — land raw as-is with audit columns (`bronze_claims`, `bronze_policyholders`)
-- MAGIC - **Silver** — cleaned/typed + derived customer fields (`silver_claims`, `silver_policyholders`)
-- MAGIC - **Gold** — enriched fraud fact + region aggregate (`gold_fraud_claims`, `gold_fraud_by_region`)
-- MAGIC
-- MAGIC The Gold tables are what Genie, the app, and Visual Data Prep consume.
-- MAGIC
-- MAGIC > Run `01_setup` and `02_generate_data` first. Uses the warehouse's **default catalog**
-- MAGIC > (add a `USE CATALOG ...;` line here only if you pinned a specific one in `01`).

-- COMMAND ----------

-- USE CATALOG <your_catalog>;   -- only if you pinned one in 01_setup
USE SCHEMA fraud_analytics;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## Step 1 · Bronze (land raw + audit columns)

-- COMMAND ----------

CREATE OR REPLACE TABLE bronze_claims AS
SELECT *, current_timestamp() AS _ingested_at, 'raw_claims' AS _source
FROM raw_claims;

CREATE OR REPLACE TABLE bronze_policyholders AS
SELECT *, current_timestamp() AS _ingested_at, 'raw_policyholders' AS _source
FROM raw_policyholders;

-- COMMAND ----------

SELECT
  (SELECT count(*) FROM bronze_claims)        AS bronze_claims,
  (SELECT count(*) FROM bronze_policyholders) AS bronze_policyholders;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## Step 2 · Silver (clean + type + derive)

-- COMMAND ----------

CREATE OR REPLACE TABLE silver_policyholders AS
SELECT
  policyholder_id, full_name, gender,
  initcap(trim(region))                 AS region,
  cast(credit_score AS int)             AS credit_score,
  cast(tenure_years AS int)             AS tenure_years,
  cast(customer_age AS int)             AS customer_age,
  cast(customer_since AS date)          AS customer_since
FROM bronze_policyholders;

CREATE OR REPLACE TABLE silver_claims AS
SELECT
  claim_id, policyholder_id, policy_type, claim_type, channel,
  cast(claim_amount AS decimal(12,2))   AS claim_amount,
  cast(claim_date AS date)              AS claim_date,
  cast(report_date AS date)             AS report_date,
  greatest(cast(report_lag_days AS int), 0) AS report_lag_days,
  cast(num_prior_claims AS int)         AS num_prior_claims,
  cast(witnesses AS int)                AS witnesses,
  police_report_filed,
  claim_status,
  cast(is_fraud AS int)                 AS is_fraud
FROM bronze_claims
WHERE claim_amount IS NOT NULL AND claim_amount > 0;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## Step 3 · Gold — enriched fraud fact (four risk flags + fraud_risk_score 0-4)

-- COMMAND ----------

CREATE OR REPLACE TABLE gold_fraud_claims AS
SELECT
  c.claim_id, c.policyholder_id, c.policy_type, c.claim_type, p.region, c.channel,
  c.claim_date, c.report_date, c.report_lag_days, c.claim_amount,
  c.num_prior_claims, c.witnesses, c.police_report_filed, c.claim_status,
  p.customer_age, p.tenure_years, p.credit_score, p.gender,
  (c.claim_amount > 20000)  AS high_value_flag,
  (c.report_lag_days <= 2)  AS fast_report_flag,
  (p.tenure_years < 1)      AS new_customer_flag,
  (p.credit_score < 500)    AS low_credit_flag,
  cast((c.claim_amount > 20000) AS int)
    + cast((c.report_lag_days <= 2) AS int)
    + cast((p.tenure_years < 1) AS int)
    + cast((p.credit_score < 500) AS int) AS fraud_risk_score,
  date_trunc('month', c.claim_date) AS claim_month,
  c.is_fraud
FROM silver_claims c
LEFT JOIN silver_policyholders p USING (policyholder_id);

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## Step 4 · Gold — region/policy aggregate (for Genie + dashboards)

-- COMMAND ----------

CREATE OR REPLACE TABLE gold_fraud_by_region AS
SELECT
  region, policy_type,
  count(*)                   AS total_claims,
  sum(claim_amount)          AS total_amount,
  sum(is_fraud)              AS fraud_claims,
  sum(is_fraud) / count(*)   AS fraud_rate,
  avg(fraud_risk_score)      AS avg_fraud_risk_score
FROM gold_fraud_claims
GROUP BY region, policy_type
ORDER BY fraud_rate DESC;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## Step 5 · Verify

-- COMMAND ----------

SELECT
  count(*)                                               AS total_claims,
  sum(is_fraud)                                          AS fraud_claims,
  round(sum(is_fraud)/count(*), 4)                       AS fraud_rate,
  sum(CASE WHEN fraud_risk_score >= 3 THEN 1 ELSE 0 END) AS high_risk_claims
FROM gold_fraud_claims;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ### ✅ Medallion complete
-- MAGIC Tables in **`allianz_lab.fraud_analytics`**: `gold_fraud_claims`, `gold_fraud_by_region`
-- MAGIC (+ bronze/silver). Next: build the **Genie Space** (notebook `05`) over the Gold tables.

-- Databricks notebook source
-- MAGIC %md
-- MAGIC # 00 · SQL-only Setup (runs on a SQL Warehouse — no cluster needed)
-- MAGIC
-- MAGIC This notebook does the **entire** data setup in pure SQL, so it runs on the lab's
-- MAGIC **Serverless SQL Warehouse** (the lab has no all-purpose Python cluster). Attach this
-- MAGIC notebook to the SQL Warehouse and click **Run all**.
-- MAGIC
-- MAGIC It will:
-- MAGIC 1. Create catalog **`allianz_lab`** and schema **`fraud_analytics`**.
-- MAGIC 2. Generate **1,500 policyholders** and **5,000 claims** of synthetic data with SQL
-- MAGIC    (with a learnable fraud signal — no Python/Faker needed).
-- MAGIC 3. Build **bronze → silver → gold** tables, including `gold_fraud_claims` and
-- MAGIC    `gold_fraud_by_region` that Genie, the app, and Visual Data Prep consume.
-- MAGIC
-- MAGIC > If your lab user cannot create a catalog, change `allianz_lab` below to a catalog you
-- MAGIC > can write to (e.g. `hive_metastore`) — everything else is unqualified via `USE`.

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## Step 1 · Catalog + schema

-- COMMAND ----------

CREATE CATALOG IF NOT EXISTS allianz_lab;

-- COMMAND ----------

CREATE SCHEMA IF NOT EXISTS allianz_lab.fraud_analytics;

-- COMMAND ----------

USE CATALOG allianz_lab;
USE SCHEMA fraud_analytics;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## Step 2 · Generate the `policyholders` dimension (1,500 rows, pure SQL)
-- MAGIC Deterministic-ish synthetic customers: region, tenure, credit score, demographics.

-- COMMAND ----------

CREATE OR REPLACE TABLE silver_policyholders AS
WITH base AS (
  SELECT
    id,
    concat('PH', cast(100000 + id AS string))                               AS policyholder_id,
    element_at(array('London','South East','North West','Scotland','Wales',
                     'Midlands','South West','North East','Yorkshire','Northern Ireland'),
               cast(floor(rand(id*7+1) * 10) AS int) + 1)                    AS region,
    element_at(array('Male','Female','Other'),
               cast(floor(rand(id*7+2) * 3) AS int) + 1)                     AS gender,
    cast(300 + floor(rand(id*7+3) * 550) AS int)                            AS credit_score,
    cast(floor(rand(id*7+4) * 10) + 1 AS int)                               AS tenure_years,
    cast(18 + floor(rand(id*7+5) * 67) AS int)                              AS customer_age
  FROM range(1500) AS t(id)
)
SELECT
  policyholder_id,
  concat('Customer ', cast(id AS string))  AS full_name,
  gender,
  region,
  credit_score,
  tenure_years,
  customer_age,
  date_sub(current_date(), cast(tenure_years * 365 AS int)) AS customer_since
FROM base;

-- COMMAND ----------

SELECT count(*) AS policyholders FROM silver_policyholders;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## Step 3 · Generate the `claims` fact (5,000 rows, pure SQL)
-- MAGIC Fraud (~7%) is injected to correlate with **higher amounts**, **faster reporting**,
-- MAGIC **newer customers** and **lower credit** — so the label is learnable in Genie/ML.

-- COMMAND ----------

CREATE OR REPLACE TABLE silver_claims AS
WITH base AS (
  SELECT
    id,
    concat('CLM', cast(500000 + id AS string))  AS claim_id,
    -- pick a policyholder 1..1500
    concat('PH', cast(100000 + cast(floor(rand(id*11+1) * 1500) AS int) AS string)) AS policyholder_id,
    element_at(array('Auto','Home','Health','Travel','Life','Commercial'),
               cast(floor(rand(id*11+2) * 6) AS int) + 1)  AS policy_type,
    element_at(array('Branch','Online','Broker','Call Center','Mobile App'),
               cast(floor(rand(id*11+3) * 5) AS int) + 1)  AS channel,
    -- fraud flag ~7%
    CASE WHEN rand(id*11+4) < 0.07 THEN 1 ELSE 0 END       AS is_fraud,
    rand(id*11+5)                                          AS r_amt,
    rand(id*11+6)                                          AS r_lag,
    cast(floor(rand(id*11+7) * 730) AS int)                AS claim_offset_days,
    cast(floor(rand(id*11+8) * 8)   AS int)                AS num_prior_claims,
    cast(floor(rand(id*11+9) * 4)   AS int)                AS witnesses
  FROM range(5000) AS t(id)
),
typed AS (
  SELECT
    *,
    -- base amount by policy type
    CASE policy_type
      WHEN 'Auto' THEN 4000 WHEN 'Home' THEN 8000 WHEN 'Health' THEN 3000
      WHEN 'Travel' THEN 1500 WHEN 'Life' THEN 50000 ELSE 25000 END AS base_amt,
    -- claim type per policy line
    CASE policy_type
      WHEN 'Auto'       THEN element_at(array('Collision','Theft','Windscreen','Third Party','Fire'), cast(floor(rand(id*13+1)*5) AS int)+1)
      WHEN 'Home'       THEN element_at(array('Flood','Burglary','Fire','Storm','Accidental Damage'), cast(floor(rand(id*13+2)*5) AS int)+1)
      WHEN 'Health'     THEN element_at(array('Hospitalisation','Outpatient','Dental','Optical'),     cast(floor(rand(id*13+3)*4) AS int)+1)
      WHEN 'Travel'     THEN element_at(array('Cancellation','Medical','Lost Luggage','Delay'),       cast(floor(rand(id*13+4)*4) AS int)+1)
      WHEN 'Life'       THEN element_at(array('Death Benefit','Critical Illness'),                    cast(floor(rand(id*13+5)*2) AS int)+1)
      ELSE                   element_at(array('Liability','Property Damage','Business Interruption'), cast(floor(rand(id*13+6)*3) AS int)+1)
    END AS claim_type
  FROM base
)
SELECT
  claim_id,
  policyholder_id,
  policy_type,
  claim_type,
  channel,
  -- fraud claims skew larger (1.8x-3.5x); use gamma-ish via base * (0.5..2) then fraud multiplier
  cast(round(base_amt * (0.5 + r_amt * 1.5) * (CASE WHEN is_fraud=1 THEN 1.8 + rand(id*17+1)*1.7 ELSE 1 END), 2) AS decimal(12,2)) AS claim_amount,
  date_add(date('2023-01-01'), claim_offset_days)                                    AS claim_date,
  -- fraud reports faster: 0-2 days vs 0-29 days
  date_add(date_add(date('2023-01-01'), claim_offset_days),
           CASE WHEN is_fraud=1 THEN cast(floor(r_lag*3) AS int) ELSE cast(floor(r_lag*30) AS int) END) AS report_date,
  CASE WHEN is_fraud=1 THEN cast(floor(r_lag*3) AS int) ELSE cast(floor(r_lag*30) AS int) END AS report_lag_days,
  num_prior_claims,
  witnesses,
  CASE WHEN rand(id*19+1) < (CASE WHEN is_fraud=1 THEN 0.3 ELSE 0.7 END) THEN true ELSE false END AS police_report_filed,
  element_at(array('Approved','Rejected','Pending','Under Review'), cast(floor(rand(id*19+2)*4) AS int)+1) AS claim_status,
  is_fraud
FROM typed;

-- COMMAND ----------

SELECT count(*) AS claims, round(avg(is_fraud), 4) AS fraud_rate FROM silver_claims;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## Step 4 · Gold — enriched fraud fact + region aggregate
-- MAGIC Joins claims to policyholders and derives the four risk flags + `fraud_risk_score` (0-4).

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

CREATE OR REPLACE TABLE gold_fraud_by_region AS
SELECT
  region, policy_type,
  count(*)                       AS total_claims,
  sum(claim_amount)              AS total_amount,
  sum(is_fraud)                  AS fraud_claims,
  sum(is_fraud) / count(*)       AS fraud_rate,
  avg(fraud_risk_score)          AS avg_fraud_risk_score
FROM gold_fraud_claims
GROUP BY region, policy_type
ORDER BY fraud_rate DESC;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## Step 5 · Verify

-- COMMAND ----------

SELECT
  count(*)                                              AS total_claims,
  sum(is_fraud)                                         AS fraud_claims,
  round(sum(is_fraud)/count(*), 4)                      AS fraud_rate,
  sum(CASE WHEN fraud_risk_score >= 3 THEN 1 ELSE 0 END) AS high_risk_claims
FROM gold_fraud_claims;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ### ✅ Setup complete
-- MAGIC Your tables live in **`allianz_lab.fraud_analytics`**:
-- MAGIC `silver_claims`, `silver_policyholders`, `gold_fraud_claims`, `gold_fraud_by_region`.
-- MAGIC
-- MAGIC Next: build the **Genie Space** over `gold_fraud_claims` + `gold_fraud_by_region`
-- MAGIC (notebook `05`), or explore in **Visual Data Prep** / the app — all on the SQL Warehouse.

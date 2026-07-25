-- Databricks notebook source
-- MAGIC %md
-- MAGIC # 02 · Generate Synthetic Data (SQL-only)
-- MAGIC
-- MAGIC Generates a realistic, **fraud-labelled insurance** dataset with **pure SQL** (no Python/Faker),
-- MAGIC so it runs on the **SQL Warehouse**. Creates two raw tables in `allianz_lab.fraud_analytics`:
-- MAGIC
-- MAGIC | Table | Rows | Grain |
-- MAGIC |-------|------|-------|
-- MAGIC | `raw_policyholders` | 1,500 | one row per customer |
-- MAGIC | `raw_claims`        | 5,000 | one row per claim (carries the `is_fraud` label) |
-- MAGIC
-- MAGIC Fraud (~7%) is injected to correlate with **higher amounts**, **faster reporting**, **newer
-- MAGIC customers** and **lower credit** — so it's learnable in Genie/ML later.
-- MAGIC
-- MAGIC > Run `01_setup` first. This uses the warehouse's **default catalog** (same as `01`). If you
-- MAGIC > pinned a specific catalog in `01`, add the same `USE CATALOG ...;` line in Step 0 below.

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## Step 0 · Use the workshop schema (in the current default catalog)

-- COMMAND ----------

-- USE CATALOG <your_catalog>;   -- only if you pinned one in 01_setup
USE SCHEMA fraud_analytics;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## Step 1 · Generate `raw_policyholders` (1,500 rows)

-- COMMAND ----------

CREATE OR REPLACE TABLE raw_policyholders AS
WITH base AS (
  SELECT
    id,
    concat('PH', cast(100000 + id AS string))                               AS policyholder_id,
    element_at(array('London','South East','North West','Scotland','Wales',
                     'Midlands','South West','North East','Yorkshire','Northern Ireland'),
               cast(floor((pmod(hash(id, 7, 1), 1000000) / 1000000.0) * 10) AS int) + 1)                    AS region,
    element_at(array('Male','Female','Other'),
               cast(floor((pmod(hash(id, 7, 2), 1000000) / 1000000.0) * 3) AS int) + 1)                     AS gender,
    cast(300 + floor((pmod(hash(id, 7, 3), 1000000) / 1000000.0) * 550) AS int)                            AS credit_score,
    cast(floor((pmod(hash(id, 7, 4), 1000000) / 1000000.0) * 10) + 1 AS int)                               AS tenure_years,
    cast(18 + floor((pmod(hash(id, 7, 5), 1000000) / 1000000.0) * 67) AS int)                              AS customer_age
  FROM range(1500) AS t(id)
)
SELECT
  policyholder_id,
  concat('Customer ', cast(id AS string))                   AS full_name,
  gender,
  region,
  credit_score,
  tenure_years,
  customer_age,
  date_sub(current_date(), cast(tenure_years * 365 AS int)) AS customer_since
FROM base;

-- COMMAND ----------

SELECT count(*) AS policyholders FROM raw_policyholders;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## Step 2 · Generate `raw_claims` (5,000 rows, ~7% fraud)

-- COMMAND ----------

CREATE OR REPLACE TABLE raw_claims AS
WITH base AS (
  SELECT
    id,
    concat('CLM', cast(500000 + id AS string))  AS claim_id,
    concat('PH', cast(100000 + cast(floor((pmod(hash(id, 11, 1), 1000000) / 1000000.0) * 1500) AS int) AS string)) AS policyholder_id,
    element_at(array('Auto','Home','Health','Travel','Life','Commercial'),
               cast(floor((pmod(hash(id, 11, 2), 1000000) / 1000000.0) * 6) AS int) + 1)  AS policy_type,
    element_at(array('Branch','Online','Broker','Call Center','Mobile App'),
               cast(floor((pmod(hash(id, 11, 3), 1000000) / 1000000.0) * 5) AS int) + 1)  AS channel,
    CASE WHEN (pmod(hash(id, 11, 4), 1000000) / 1000000.0) < 0.07 THEN 1 ELSE 0 END       AS is_fraud,
    (pmod(hash(id, 11, 5), 1000000) / 1000000.0)                                          AS r_amt,
    (pmod(hash(id, 11, 6), 1000000) / 1000000.0)                                          AS r_lag,
    cast(floor((pmod(hash(id, 11, 7), 1000000) / 1000000.0) * 730) AS int)                AS claim_offset_days,
    cast(floor((pmod(hash(id, 11, 8), 1000000) / 1000000.0) * 8)   AS int)                AS num_prior_claims,
    cast(floor((pmod(hash(id, 11, 9), 1000000) / 1000000.0) * 4)   AS int)                AS witnesses
  FROM range(5000) AS t(id)
),
typed AS (
  SELECT
    *,
    CASE policy_type
      WHEN 'Auto' THEN 4000 WHEN 'Home' THEN 8000 WHEN 'Health' THEN 3000
      WHEN 'Travel' THEN 1500 WHEN 'Life' THEN 50000 ELSE 25000 END AS base_amt,
    CASE policy_type
      WHEN 'Auto'   THEN element_at(array('Collision','Theft','Windscreen','Third Party','Fire'), cast(floor((pmod(hash(id, 13, 1), 1000000) / 1000000.0)*5) AS int)+1)
      WHEN 'Home'   THEN element_at(array('Flood','Burglary','Fire','Storm','Accidental Damage'), cast(floor((pmod(hash(id, 13, 2), 1000000) / 1000000.0)*5) AS int)+1)
      WHEN 'Health' THEN element_at(array('Hospitalisation','Outpatient','Dental','Optical'),     cast(floor((pmod(hash(id, 13, 3), 1000000) / 1000000.0)*4) AS int)+1)
      WHEN 'Travel' THEN element_at(array('Cancellation','Medical','Lost Luggage','Delay'),       cast(floor((pmod(hash(id, 13, 4), 1000000) / 1000000.0)*4) AS int)+1)
      WHEN 'Life'   THEN element_at(array('Death Benefit','Critical Illness'),                    cast(floor((pmod(hash(id, 13, 5), 1000000) / 1000000.0)*2) AS int)+1)
      ELSE               element_at(array('Liability','Property Damage','Business Interruption'), cast(floor((pmod(hash(id, 13, 6), 1000000) / 1000000.0)*3) AS int)+1)
    END AS claim_type
  FROM base
)
SELECT
  claim_id,
  policyholder_id,
  policy_type,
  claim_type,
  channel,
  cast(round(base_amt * (0.5 + r_amt * 1.5)
       * (CASE WHEN is_fraud=1 THEN 1.8 + (pmod(hash(id, 17, 1), 1000000) / 1000000.0)*1.7 ELSE 1 END), 2) AS decimal(12,2)) AS claim_amount,
  date_add(date('2023-01-01'), claim_offset_days)  AS claim_date,
  date_add(date_add(date('2023-01-01'), claim_offset_days),
           CASE WHEN is_fraud=1 THEN cast(floor(r_lag*3) AS int) ELSE cast(floor(r_lag*30) AS int) END) AS report_date,
  CASE WHEN is_fraud=1 THEN cast(floor(r_lag*3) AS int) ELSE cast(floor(r_lag*30) AS int) END AS report_lag_days,
  num_prior_claims,
  witnesses,
  CASE WHEN (pmod(hash(id, 19, 1), 1000000) / 1000000.0) < (CASE WHEN is_fraud=1 THEN 0.3 ELSE 0.7 END) THEN true ELSE false END AS police_report_filed,
  element_at(array('Approved','Rejected','Pending','Under Review'), cast(floor((pmod(hash(id, 19, 2), 1000000) / 1000000.0)*4) AS int)+1) AS claim_status,
  is_fraud
FROM typed;

-- COMMAND ----------

SELECT count(*) AS claims, round(avg(is_fraud), 4) AS fraud_rate FROM raw_claims;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ### ✅ Data generated
-- MAGIC Next: run **`03_load_to_bronze`** to build the Bronze → Silver → Gold tables.

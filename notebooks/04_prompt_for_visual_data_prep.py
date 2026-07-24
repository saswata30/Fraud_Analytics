# Databricks notebook source
# MAGIC %md
# MAGIC # 04 · Prompt for Databricks Visual Data Prep (Bronze → Silver → Gold)
# MAGIC
# MAGIC **Databricks Visual Data Prep** (Lakeflow Designer / low-code data preparation) lets you build a
# MAGIC transformation pipeline with a visual, drag-and-drop canvas — no PySpark required. This notebook is a
# MAGIC **prompt playbook**: copy the prompts below into the Visual Data Prep assistant to build the pipeline,
# MAGIC then schedule it as a **Lakeflow Job**.
# MAGIC
# MAGIC You will produce:
# MAGIC - `silver_claims` — cleaned, deduplicated, typed claims with data-quality rules enforced
# MAGIC - `silver_policyholders` — cleaned policyholder dimension
# MAGIC - `gold_fraud_claims` — analytics-ready, enriched fact table joined to policyholders, with derived fraud features
# MAGIC - `gold_fraud_by_region` — an aggregate for dashboards / Genie
# MAGIC
# MAGIC > **This notebook contains no executable transformation code by design.** It is the instruction set you
# MAGIC > paste into Visual Data Prep. A reference SQL appendix is included at the end if you prefer to validate manually.

# COMMAND ----------

# MAGIC %md
# MAGIC ## How to run this in Visual Data Prep
# MAGIC
# MAGIC 1. In the left sidebar, click **Data Engineering → Data Preparation** (Visual Data Prep / Lakeflow Designer).
# MAGIC 2. Click **Create → Data preparation pipeline**.
# MAGIC 3. Set the **source** to `allianz_workshop.fraud_analytics.bronze_claims` (and `bronze_policyholders`).
# MAGIC 4. Open the **Assistant** panel (✨ icon) and paste the prompts from the sections below, one stage at a time.
# MAGIC 5. Review the auto-generated transformation steps on the canvas, adjust as needed, and **Preview**.
# MAGIC 6. Set the **destination** table for each stage (Silver, then Gold).
# MAGIC 7. Click **Create job / Schedule** to publish it as a **Lakeflow pipeline job** (see Step 5 below).

# COMMAND ----------

# MAGIC %md
# MAGIC ## Prompt 1 · Bronze → Silver (clean `claims`)
# MAGIC
# MAGIC Paste this into the Visual Data Prep assistant with `bronze_claims` as the input:
# MAGIC
# MAGIC ```
# MAGIC Clean the bronze_claims table into a silver_claims table:
# MAGIC - Remove exact duplicate rows.
# MAGIC - Trim whitespace and standardise the `region` column to Title Case.
# MAGIC - Drop rows where `claim_amount` is null or less than or equal to 0.
# MAGIC - Cast `claim_date` and `report_date` to DATE, `claim_amount` to DECIMAL(12,2),
# MAGIC   and `is_fraud` to INTEGER.
# MAGIC - Keep report_lag_days but flag any negative lag as a data error (set to 0).
# MAGIC - Drop the raw audit columns _ingested_at and _source_file are retained.
# MAGIC - Output columns: claim_id, policyholder_id, policy_type, claim_type, region,
# MAGIC   channel, claim_date, report_date, report_lag_days, claim_amount,
# MAGIC   num_prior_claims, witnesses, police_report_filed, claim_status, is_fraud.
# MAGIC ```

# COMMAND ----------

# MAGIC %md
# MAGIC ## Prompt 2 · Bronze → Silver (clean `policyholders`)
# MAGIC
# MAGIC ```
# MAGIC Clean bronze_policyholders into silver_policyholders:
# MAGIC - Remove duplicates on policyholder_id (keep first).
# MAGIC - Standardise region to Title Case and trim whitespace.
# MAGIC - Cast date_of_birth and customer_since to DATE.
# MAGIC - Derive a `customer_age` column from date_of_birth.
# MAGIC - Derive `tenure_years` = years between customer_since and current date.
# MAGIC - Drop email and phone (PII not needed for analytics).
# MAGIC ```

# COMMAND ----------

# MAGIC %md
# MAGIC ## Prompt 3 · Silver → Gold (enriched fraud fact table)
# MAGIC
# MAGIC ```
# MAGIC Create gold_fraud_claims by joining silver_claims to silver_policyholders on
# MAGIC policyholder_id (left join). Then add these derived features:
# MAGIC - `high_value_flag` = claim_amount > 20000.
# MAGIC - `fast_report_flag` = report_lag_days <= 2.
# MAGIC - `new_customer_flag` = tenure_years < 1.
# MAGIC - `low_credit_flag` = credit_score < 500.
# MAGIC - `fraud_risk_score` = sum of the four flags above (0 to 4).
# MAGIC - `claim_month` = date_trunc('month', claim_date).
# MAGIC Keep is_fraud as the ground-truth label. Output an analytics-ready table.
# MAGIC ```

# COMMAND ----------

# MAGIC %md
# MAGIC ## Prompt 4 · Gold aggregate for dashboards / Genie
# MAGIC
# MAGIC ```
# MAGIC Create gold_fraud_by_region aggregating gold_fraud_claims by region and policy_type:
# MAGIC - total_claims = count of claims
# MAGIC - total_amount = sum of claim_amount
# MAGIC - fraud_claims = sum of is_fraud
# MAGIC - fraud_rate = fraud_claims / total_claims
# MAGIC - avg_fraud_risk_score = average of fraud_risk_score
# MAGIC Order by fraud_rate descending.
# MAGIC ```

# COMMAND ----------

# MAGIC %md
# MAGIC ## Prompt 5 · Data-quality checks (expectations)
# MAGIC
# MAGIC In Visual Data Prep, add **data quality expectations** on the Silver/Gold steps. Paste:
# MAGIC
# MAGIC ```
# MAGIC Add data quality checks to silver_claims:
# MAGIC - claim_id must be unique and not null (fail pipeline if violated).
# MAGIC - claim_amount must be > 0 (drop rows that violate).
# MAGIC - is_fraud must be in (0, 1) (fail pipeline if violated).
# MAGIC - report_date must be >= claim_date (quarantine rows that violate).
# MAGIC - region must be in the known list of UK regions (warn only).
# MAGIC ```

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 5 · Publish as a Lakeflow Job (pipeline)
# MAGIC
# MAGIC After the canvas is built and previewed:
# MAGIC 1. Click **Schedule / Create pipeline** in the Visual Data Prep toolbar.
# MAGIC 2. Name it **`fraud_analytics_bronze_to_gold`**.
# MAGIC 3. Set target catalog/schema to `allianz_workshop.fraud_analytics`.
# MAGIC 4. Choose **Serverless** compute.
# MAGIC 5. Add a schedule (e.g. daily) or leave as triggered.
# MAGIC 6. Click **Create**. The pipeline appears under **Workflows → Lakeflow Pipelines**.
# MAGIC 7. Click **Run now** and confirm all three layers (Silver, Gold, aggregate) populate.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Appendix · Reference SQL (optional manual validation)
# MAGIC
# MAGIC If you'd rather validate the logic without the visual tool, the equivalent SQL is below. It produces the
# MAGIC same Silver/Gold tables. **Visual Data Prep is the intended path for the workshop** — this is just a fallback.

# COMMAND ----------

# MAGIC %md
# MAGIC ```sql
# MAGIC -- Silver claims
# MAGIC CREATE OR REPLACE TABLE allianz_workshop.fraud_analytics.silver_claims AS
# MAGIC SELECT DISTINCT
# MAGIC   claim_id, policyholder_id, policy_type, claim_type,
# MAGIC   INITCAP(TRIM(region))              AS region,
# MAGIC   channel,
# MAGIC   CAST(claim_date  AS DATE)          AS claim_date,
# MAGIC   CAST(report_date AS DATE)          AS report_date,
# MAGIC   GREATEST(report_lag_days, 0)       AS report_lag_days,
# MAGIC   CAST(claim_amount AS DECIMAL(12,2)) AS claim_amount,
# MAGIC   num_prior_claims, witnesses, police_report_filed, claim_status,
# MAGIC   CAST(is_fraud AS INT)              AS is_fraud
# MAGIC FROM allianz_workshop.fraud_analytics.bronze_claims
# MAGIC WHERE claim_amount IS NOT NULL AND claim_amount > 0;
# MAGIC
# MAGIC -- Silver policyholders
# MAGIC CREATE OR REPLACE TABLE allianz_workshop.fraud_analytics.silver_policyholders AS
# MAGIC SELECT
# MAGIC   policyholder_id, full_name, gender,
# MAGIC   CAST(date_of_birth AS DATE)  AS date_of_birth,
# MAGIC   INITCAP(TRIM(region))        AS region,
# MAGIC   CAST(customer_since AS DATE) AS customer_since,
# MAGIC   credit_score,
# MAGIC   FLOOR(DATEDIFF(current_date(), date_of_birth)/365.25)  AS customer_age,
# MAGIC   FLOOR(DATEDIFF(current_date(), customer_since)/365.25) AS tenure_years
# MAGIC FROM (
# MAGIC   SELECT *, ROW_NUMBER() OVER (PARTITION BY policyholder_id ORDER BY _ingested_at) rn
# MAGIC   FROM allianz_workshop.fraud_analytics.bronze_policyholders
# MAGIC ) WHERE rn = 1;
# MAGIC
# MAGIC -- Gold enriched fact
# MAGIC CREATE OR REPLACE TABLE allianz_workshop.fraud_analytics.gold_fraud_claims AS
# MAGIC SELECT
# MAGIC   c.*,
# MAGIC   p.customer_age, p.tenure_years, p.credit_score, p.gender,
# MAGIC   (c.claim_amount > 20000)        AS high_value_flag,
# MAGIC   (c.report_lag_days <= 2)        AS fast_report_flag,
# MAGIC   (p.tenure_years < 1)            AS new_customer_flag,
# MAGIC   (p.credit_score < 500)          AS low_credit_flag,
# MAGIC   CAST((c.claim_amount > 20000) AS INT)
# MAGIC     + CAST((c.report_lag_days <= 2) AS INT)
# MAGIC     + CAST((p.tenure_years < 1) AS INT)
# MAGIC     + CAST((p.credit_score < 500) AS INT) AS fraud_risk_score,
# MAGIC   DATE_TRUNC('month', c.claim_date) AS claim_month
# MAGIC FROM allianz_workshop.fraud_analytics.silver_claims c
# MAGIC LEFT JOIN allianz_workshop.fraud_analytics.silver_policyholders p USING (policyholder_id);
# MAGIC
# MAGIC -- Gold aggregate
# MAGIC CREATE OR REPLACE TABLE allianz_workshop.fraud_analytics.gold_fraud_by_region AS
# MAGIC SELECT region, policy_type,
# MAGIC   COUNT(*)                          AS total_claims,
# MAGIC   SUM(claim_amount)                 AS total_amount,
# MAGIC   SUM(is_fraud)                     AS fraud_claims,
# MAGIC   SUM(is_fraud)/COUNT(*)            AS fraud_rate,
# MAGIC   AVG(fraud_risk_score)             AS avg_fraud_risk_score
# MAGIC FROM allianz_workshop.fraud_analytics.gold_fraud_claims
# MAGIC GROUP BY region, policy_type
# MAGIC ORDER BY fraud_rate DESC;
# MAGIC ```

# COMMAND ----------

# MAGIC %md
# MAGIC ### ✅ Pipeline built
# MAGIC Next: open **`05_genie_space_setup`** to create a Genie Space over the Gold tables.

# Databricks notebook source
# MAGIC %md
# MAGIC # 03 · Load Raw → Bronze
# MAGIC
# MAGIC Ingests the raw CSV and Parquet files from `raw/input` into **Bronze Delta tables**, applying the
# MAGIC classic Medallion Bronze pattern: **land data as-is**, keep it schema-flexible, and add lightweight
# MAGIC **audit columns** (`_ingested_at`, `_source_file`). No cleaning happens here — that's Silver's job.
# MAGIC
# MAGIC | Source file | Bronze table |
# MAGIC |-------------|--------------|
# MAGIC | `claims.csv` | `bronze_claims` |
# MAGIC | `policyholders.parquet` | `bronze_policyholders` |
# MAGIC
# MAGIC > **How to run:** Run `01_setup` and `02_generate_data` first, then `Run all`.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 1 · Configuration

# COMMAND ----------

CATALOG       = "allianz_workshop"   # or "default"
SCHEMA        = "fraud_analytics"
VOLUME        = "raw"
VOLUME_SUBDIR = "input"

INPUT_PATH = f"/Volumes/{CATALOG}/{SCHEMA}/{VOLUME}/{VOLUME_SUBDIR}"

spark.sql(f"USE CATALOG {CATALOG}")
spark.sql(f"USE SCHEMA {SCHEMA}")
print(f"Reading from: {INPUT_PATH}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 2 · Imports

# COMMAND ----------

from pyspark.sql import functions as F

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 3 · Load `claims.csv` → `bronze_claims`
# MAGIC We read the CSV with header + schema inference, then add audit columns and write as a managed Delta table.

# COMMAND ----------

claims_df = (
    spark.read
    .option("header", "true")
    .option("inferSchema", "true")
    .csv(f"{INPUT_PATH}/claims.csv")
    .withColumn("_ingested_at", F.current_timestamp())
    .withColumn("_source_file", F.lit("claims.csv"))
)

(claims_df.write
    .format("delta")
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable(f"{CATALOG}.{SCHEMA}.bronze_claims"))

print(f"✅ bronze_claims: {spark.table('bronze_claims').count():,} rows")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 4 · Load `policyholders.parquet` → `bronze_policyholders`

# COMMAND ----------

holders_df = (
    spark.read
    .parquet(f"{INPUT_PATH}/policyholders.parquet")
    .withColumn("_ingested_at", F.current_timestamp())
    .withColumn("_source_file", F.lit("policyholders.parquet"))
)

(holders_df.write
    .format("delta")
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable(f"{CATALOG}.{SCHEMA}.bronze_policyholders"))

print(f"✅ bronze_policyholders: {spark.table('bronze_policyholders').count():,} rows")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 5 · Quick sanity check
# MAGIC Confirm the tables exist and preview a few rows. Note the raw data-quality issues (nulls, negatives,
# MAGIC whitespace, duplicates) are intentionally preserved for the Silver cleaning step.

# COMMAND ----------

display(spark.sql(f"SHOW TABLES IN {CATALOG}.{SCHEMA}"))

# COMMAND ----------

display(spark.table("bronze_claims").limit(10))

# COMMAND ----------

# MAGIC %md
# MAGIC ### ✅ Bronze load complete
# MAGIC Next: open **`04_prompt_for_visual_data_prep`** to build the Bronze→Silver→Gold pipeline
# MAGIC in Databricks **Visual Data Prep**.

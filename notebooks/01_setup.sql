-- Databricks notebook source
-- MAGIC %md
-- MAGIC # 01 · Setup — Catalog & Schema (SQL-only, runs on a SQL Warehouse)
-- MAGIC
-- MAGIC This notebook prepares the Unity Catalog objects for the **Fraud Analytics** workshop using
-- MAGIC **pure SQL**, so it runs on the lab's **Serverless SQL Warehouse** (no all-purpose cluster
-- MAGIC needed). Attach to the SQL Warehouse and click **Run all**.
-- MAGIC
-- MAGIC Creates schema **`fraud_analytics`** in the **default catalog** the SQL Warehouse is already
-- MAGIC connected to (this lab does **not** allow creating new catalogs). Nothing is hard-coded — the
-- MAGIC schema lands in whatever catalog is current, and notebooks `02`/`03` inherit it.
-- MAGIC
-- MAGIC > Want a specific catalog? Uncomment the `USE CATALOG ...` line in Step 1 and set it to one you
-- MAGIC > can write to. Otherwise leave it — the current default catalog is used.

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## Step 1 · (Optional) pick a catalog — otherwise use the default
-- MAGIC The default catalog your warehouse is attached to is used automatically. To pin a specific
-- MAGIC one, uncomment and edit the line below.

-- COMMAND ----------

-- USE CATALOG <your_catalog>;   -- optional: only if you want a specific catalog
SELECT current_catalog() AS default_catalog;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## Step 2 · Create the schema in the current catalog

-- COMMAND ----------

CREATE SCHEMA IF NOT EXISTS fraud_analytics;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## Step 3 · Make it the default schema for this session

-- COMMAND ----------

USE SCHEMA fraud_analytics;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## Step 4 · Create the `raw` volume
-- MAGIC A **managed volume** named `raw` holds file-based data: `02` can land CSV/Parquet under
-- MAGIC `raw/input`, and the **app's document upload** writes to `raw/input/userdata`. The app fails to
-- MAGIC accept uploads if this volume doesn't exist, so create it here.

-- COMMAND ----------

CREATE VOLUME IF NOT EXISTS raw;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## Step 5 · Confirm where the tables will live

-- COMMAND ----------

SELECT current_catalog() AS catalog, current_schema() AS schema;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ### ✅ Setup complete
-- MAGIC Next: run **`02_generate_data`** to create the synthetic insurance fraud dataset.

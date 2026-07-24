-- Databricks notebook source
-- MAGIC %md
-- MAGIC # 01 · Setup — Catalog & Schema (SQL-only, runs on a SQL Warehouse)
-- MAGIC
-- MAGIC This notebook prepares the Unity Catalog objects for the **Fraud Analytics** workshop using
-- MAGIC **pure SQL**, so it runs on the lab's **Serverless SQL Warehouse** (no all-purpose cluster
-- MAGIC needed). Attach to the SQL Warehouse and click **Run all**.
-- MAGIC
-- MAGIC Creates catalog **`allianz_lab`** and schema **`fraud_analytics`**.
-- MAGIC
-- MAGIC > If your lab user cannot create a catalog, change `allianz_lab` below to a catalog you can
-- MAGIC > write to (e.g. `hive_metastore`). Keep the same catalog name in notebooks `02` and `03`.

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## Step 1 · Create the catalog

-- COMMAND ----------

CREATE CATALOG IF NOT EXISTS allianz_lab;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## Step 2 · Create the schema

-- COMMAND ----------

CREATE SCHEMA IF NOT EXISTS allianz_lab.fraud_analytics;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## Step 3 · Make it the default for this session

-- COMMAND ----------

USE CATALOG allianz_lab;
USE SCHEMA fraud_analytics;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## Step 4 · Confirm

-- COMMAND ----------

SELECT current_catalog() AS catalog, current_schema() AS schema;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ### ✅ Setup complete
-- MAGIC Next: run **`02_generate_data`** to create the synthetic insurance fraud dataset.

# Databricks notebook source
# MAGIC %md
# MAGIC # 01 · Setup — Catalog, Schema & Volume
# MAGIC
# MAGIC This notebook prepares the Unity Catalog objects for the **Fraud Analytics** insurance workshop.
# MAGIC
# MAGIC It will:
# MAGIC 1. Try to create a catalog `allianz_workshop`. If your permissions do not allow catalog creation, it falls back to the **`default`** catalog.
# MAGIC 2. Create a schema **`fraud_analytics`** in the chosen catalog.
# MAGIC 3. Create a managed volume **`raw`** with an **`input`** sub-directory for landing raw files.
# MAGIC
# MAGIC > **How to run:** Attach to a cluster or Serverless, then `Run all`. Each activity is in its own cell so you can step through it.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 1 · Configuration
# MAGIC Change these values if you want different names. Everything downstream reads from these variables.

# COMMAND ----------

# Desired names — edit if needed
PREFERRED_CATALOG = "allianz_workshop"
FALLBACK_CATALOG  = "default"
SCHEMA            = "fraud_analytics"
VOLUME            = "raw"
VOLUME_SUBDIR     = "input"

print(f"Preferred catalog : {PREFERRED_CATALOG}")
print(f"Fallback catalog  : {FALLBACK_CATALOG}")
print(f"Schema            : {SCHEMA}")
print(f"Volume            : {VOLUME}/{VOLUME_SUBDIR}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 2 · Create (or fall back to) a catalog
# MAGIC We attempt to create `allianz_workshop`. If we lack the `CREATE CATALOG` privilege, we gracefully fall back to `default` so the workshop still works.

# COMMAND ----------

def resolve_catalog():
    """Try to create the preferred catalog; fall back to default on failure."""
    try:
        spark.sql(f"CREATE CATALOG IF NOT EXISTS {PREFERRED_CATALOG}")
        print(f"✅ Using catalog: {PREFERRED_CATALOG}")
        return PREFERRED_CATALOG
    except Exception as e:
        print(f"⚠️  Could not create '{PREFERRED_CATALOG}': {e}")
        print(f"➡️  Falling back to catalog: {FALLBACK_CATALOG}")
        return FALLBACK_CATALOG

CATALOG = resolve_catalog()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 3 · Create the schema

# COMMAND ----------

spark.sql(f"CREATE SCHEMA IF NOT EXISTS {CATALOG}.{SCHEMA}")
spark.sql(f"USE CATALOG {CATALOG}")
spark.sql(f"USE SCHEMA {SCHEMA}")
print(f"✅ Schema ready: {CATALOG}.{SCHEMA}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 4 · Create the managed volume `raw` with an `input` folder
# MAGIC The volume is where `02_generate_data` will land the raw CSV and Parquet files that `03_load_to_bronze` then ingests.

# COMMAND ----------

spark.sql(f"CREATE VOLUME IF NOT EXISTS {CATALOG}.{SCHEMA}.{VOLUME}")

volume_input_path = f"/Volumes/{CATALOG}/{SCHEMA}/{VOLUME}/{VOLUME_SUBDIR}"
dbutils.fs.mkdirs(volume_input_path)
print(f"✅ Volume input path ready: {volume_input_path}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 5 · Persist configuration for downstream notebooks
# MAGIC We store the resolved names as a task value and print a copy-paste block so every other notebook uses the same targets.

# COMMAND ----------

# Make values available to other notebooks in a job via task values
dbutils.jobs.taskValues.set(key="catalog", value=CATALOG) if hasattr(dbutils, "jobs") else None

config = {
    "catalog": CATALOG,
    "schema": SCHEMA,
    "volume": VOLUME,
    "input_path": volume_input_path,
}
print("Copy these into the other notebooks if you changed defaults:\n")
for k, v in config.items():
    print(f"  {k:12s}= {v!r}")

# COMMAND ----------

# MAGIC %md
# MAGIC ### ✅ Setup complete
# MAGIC Next: run **`02_generate_data`** to create the synthetic insurance fraud dataset.

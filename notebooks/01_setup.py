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
# MAGIC ## Step 1 · Resolve catalog + schema (works in any workspace)
# MAGIC We run the shared `_config` notebook. It tries to create a Unity Catalog
# MAGIC (`allianz_workshop`), and if you lack `CREATE CATALOG` it reuses an existing writable
# MAGIC catalog (`main`) or falls back to `hive_metastore` — so this runs cleanly in a Vocareum
# MAGIC lab, FEVM, or a demo workspace without editing anything.

# COMMAND ----------

# MAGIC %run ./_config

# COMMAND ----------

# `_config` set: CATALOG, SCHEMA, FQ, VOLUME, INPUT_PATH, USERDATA_PATH and already
# created + USE'd the schema. Confirm what we resolved to:
print(f"✅ Catalog : {CATALOG}")
print(f"✅ Schema  : {FQ}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 2 · Create the managed volume `raw` with an `input` folder
# MAGIC The volume is where `02_generate_data` will land the raw CSV and Parquet files that
# MAGIC `03_load_to_bronze` then ingests.

# COMMAND ----------

spark.sql(f"CREATE VOLUME IF NOT EXISTS {CATALOG}.{SCHEMA}.{VOLUME}")

volume_input_path = INPUT_PATH
dbutils.fs.mkdirs(volume_input_path)
print(f"✅ Volume input path ready: {volume_input_path}")

# A dedicated sub-folder for documents that end users upload via the app.
# The "Ask Genie" app lands uploaded files here (raw/input/userdata).
userdata_path = f"{volume_input_path}/userdata"
dbutils.fs.mkdirs(userdata_path)
print(f"✅ User-upload path ready:  {userdata_path}")

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
    "userdata_path": userdata_path,
}
print("Copy these into the other notebooks if you changed defaults:\n")
for k, v in config.items():
    print(f"  {k:12s}= {v!r}")

# COMMAND ----------

# MAGIC %md
# MAGIC ### ✅ Setup complete
# MAGIC Next: run **`02_generate_data`** to create the synthetic insurance fraud dataset.

# Databricks notebook source
# MAGIC %md
# MAGIC # 07 · Build & Deploy the Fraud App with Genie Code — *(optional)*
# MAGIC
# MAGIC A ready-made **React + FastAPI** Databricks App ships in this repo under **`app/`** — a dark,
# MAGIC single-page fraud workspace with a dashboard, an insurance-fraud news panel, and a docked
# MAGIC **Fraud Chatbot** (Genie + document upload) over the same Gold tables as `05`/`06`.
# MAGIC
# MAGIC The simplest path is to hand the template to **Genie Code** (the Databricks coding assistant)
# MAGIC and let it build and deploy. Just tell it the app folder and the deploy command.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Prompt for Genie Code
# MAGIC Open **Genie Code**, point it at this repo, and paste:
# MAGIC
# MAGIC ```
# MAGIC Build and deploy the app from the template in the app/ folder of this repo.
# MAGIC Do not rewrite it — reuse it as-is.
# MAGIC
# MAGIC App folder:  app/
# MAGIC Command:     cd app && python deploy.py \
# MAGIC                --profile <my-cli-profile> \
# MAGIC                --warehouse-id <my-serverless-sql-warehouse-id>
# MAGIC
# MAGIC deploy.py resolves the catalog, creates the Genie space over the Gold tables,
# MAGIC builds the frontend, deploys the app, and grants the app service principal
# MAGIC access to the catalog, schema, raw volume, warehouse, Genie space, and LLM
# MAGIC endpoint. When it finishes, give me the printed app URL.
# MAGIC ```

# COMMAND ----------

# MAGIC %md
# MAGIC ## Or run it yourself — one command
# MAGIC From a clone of this repo (local terminal, not the notebook):
# MAGIC
# MAGIC ```bash
# MAGIC cd app
# MAGIC python deploy.py \
# MAGIC   --profile      <my-cli-profile> \
# MAGIC   --warehouse-id <my-serverless-sql-warehouse-id>
# MAGIC   # optional: --catalog <catalog> --app-name fraud-analytics --genie-space-id <existing>
# MAGIC ```
# MAGIC
# MAGIC That's it — it prints the app URL when done. See **`app/DEPLOY.md`** for the full explanation
# MAGIC and a manual, step-by-step alternative.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Prerequisites
# MAGIC - Notebooks `01`→`03` have run — the **Gold tables** exist in `<catalog>.fraud_analytics`.
# MAGIC - The **Databricks CLI** is authenticated (`databricks auth profiles`) with permission to create Apps.
# MAGIC - A **Serverless SQL Warehouse ID**.
# MAGIC
# MAGIC > Uploaded documents land in the volume folder **`raw/input/userdata`**. Try it with the sample
# MAGIC > files in `docs/`, then ask the questions listed there.

# COMMAND ----------

# MAGIC %md
# MAGIC ### ✅ Workshop complete
# MAGIC Full path: **Setup → Data → Bronze/Silver/Gold → Genie (`05`) → Dashboard (`06`) → App (`07`, optional).**
# MAGIC All surfaces read the same Gold tables.

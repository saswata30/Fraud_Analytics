# Databricks notebook source
# MAGIC %md
# MAGIC # 🕵️ Fraud Analytics — Insurance Workshop (Start Here)
# MAGIC
# MAGIC Welcome! This lab goes end-to-end: **synthetic data → Gold tables → Genie → a chat app** for
# MAGIC an insurance **fraud analytics** use case — and it all runs on a **Serverless SQL Warehouse**
# MAGIC (no all-purpose cluster needed).
# MAGIC
# MAGIC Everything is in this folder (`Fraud_Analytics`).

# COMMAND ----------

# MAGIC %md
# MAGIC ## Run order
# MAGIC
# MAGIC | # | Notebook | What it does | Compute |
# MAGIC |---|----------|--------------|---------|
# MAGIC | 00 | [`notebooks/00_setup_sql`]($./00_setup_sql) | **Start here.** Creates catalog `allianz_lab`, schema `fraud_analytics`, generates the data, and builds `gold_fraud_claims` / `gold_fraud_by_region` — **pure SQL**. | SQL Warehouse |
# MAGIC | 05 | [`notebooks/05_genie_space_setup`]($./05_genie_space_setup) | Create + instruct + benchmark a Genie Space over the Gold tables. | SQL Warehouse |
# MAGIC | 04 | [`notebooks/04_prompt_for_visual_data_prep`]($./04_prompt_for_visual_data_prep) | (Optional) Visual Data Prep playbook: Bronze→Silver→Gold with data-quality checks. | Serverless / SQL |
# MAGIC | 06 | [`notebooks/06_prompt_for_chat_app`]($./06_prompt_for_chat_app) | (Optional) Build the "Fraud Chatbot" Databricks App. | App compute |

# COMMAND ----------

# MAGIC %md
# MAGIC ## How to run `00_setup_sql`
# MAGIC 1. Open [`notebooks/00_setup_sql`]($./00_setup_sql).
# MAGIC 2. Attach it to the **Serverless SQL Warehouse** (top-right compute selector).
# MAGIC 3. Click **Run all**. It creates `allianz_lab.fraud_analytics` with the claims + gold tables.
# MAGIC
# MAGIC > No cluster? That's expected in this lab — `00_setup_sql` is SQL-only precisely so it runs on
# MAGIC > the SQL Warehouse. (The older Python notebooks that needed a cluster are in git history.)

# COMMAND ----------

# MAGIC %md
# MAGIC ## What else is here
# MAGIC - **`docs/`** — documents to upload in the app's Fraud Chatbot and ask questions about
# MAGIC   (`fraud_event_report.pdf`, `eu_compliance_policy.pdf`, `genie_questions.docx`).
# MAGIC - **`data/`** — pre-generated raw CSV/Parquet (reference; `00_setup_sql` generates its own in-table).
# MAGIC - **`app/`** — the React + FastAPI Fraud Chatbot (see `app/DEPLOY.md`).
# MAGIC
# MAGIC **Have fun catching fraud! 🚨**

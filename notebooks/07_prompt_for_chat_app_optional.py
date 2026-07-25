# Databricks notebook source
# MAGIC %md
# MAGIC # 07 · Deploy the "Chat with your Data" App — *(optional)*
# MAGIC
# MAGIC A ready-made **React + FastAPI** Databricks App ships in this repo under **`app/`**. It has two
# MAGIC screens over the **same Gold tables** as the dashboard (`06`) and the Genie Space (`05`):
# MAGIC 1. **Overview** — the fraud dashboard (KPIs, trend, fraud by region/policy, risk-score distribution).
# MAGIC 2. **Ask Genie** — natural-language chat over the fraud data via the **Genie Conversation API**,
# MAGIC    plus document upload (files land in `raw/input/userdata`).
# MAGIC
# MAGIC > **This step is optional.** The dashboard (`06`) and Genie Space (`05`) already give you the full
# MAGIC > analytics experience. Deploy the app only if you want the packaged "chat + dashboard" surface.
# MAGIC >
# MAGIC > **Reuse, don't rebuild.** The `app/` folder is complete and tested — just deploy it. There is no
# MAGIC > need to regenerate it with Genie Code. (The design brief is preserved at the end of this
# MAGIC > notebook for reference only.)

# COMMAND ----------

# MAGIC %md
# MAGIC ## What it reads
# MAGIC - **Gold tables** (`03`): `gold_fraud_claims`, `gold_fraud_by_region` → power the Overview dashboard
# MAGIC   and are the tables the Genie Space answers over.
# MAGIC - **Genie Space** (`05`): the "Ask Genie" screen calls its Conversation API. You need its
# MAGIC   **Space ID** (from the URL `.../genie/rooms/<SPACE_ID>`) — or let `deploy.py` create one for you.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Prerequisites
# MAGIC - Notebooks `01`→`03` have run — the **Gold tables** exist in `<catalog>.fraud_analytics`.
# MAGIC - A **Serverless SQL Warehouse ID**.
# MAGIC - The **Databricks CLI** authenticated (`databricks auth profiles`), and permission to create **Apps**.
# MAGIC - A **Genie Space** over the Gold tables (`05`). *Optional* — `deploy.py` will create one if you
# MAGIC   don't pass `--genie-space-id`.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Deploy — one command (from the repo `app/` folder)
# MAGIC The repo's `app/deploy.py` does the whole thing: resolves the catalog, (optionally) creates the
# MAGIC Genie Space over the Gold tables, writes `app.yaml`, builds the frontend, syncs, deploys, and
# MAGIC grants the app's service principal least-privilege access.
# MAGIC
# MAGIC ```bash
# MAGIC # Run locally from a clone of this repo (not inside the notebook)
# MAGIC cd app
# MAGIC python deploy.py \
# MAGIC   --profile      <your-databricks-cli-profile> \
# MAGIC   --warehouse-id <serverless-sql-warehouse-id> \
# MAGIC   --app-name     fraud-analytics
# MAGIC   # optional: --catalog <catalog> --schema fraud_analytics --genie-space-id <existing-space-id>
# MAGIC ```
# MAGIC
# MAGIC When it finishes it prints the app URL. See **`app/DEPLOY.md`** for the full explanation and the
# MAGIC by-hand sequence.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Point the app at your Genie Space + Gold tables
# MAGIC The app is configured entirely through `app/app.yaml` env vars — `deploy.py` fills these in, but
# MAGIC set them yourself if you deploy by hand:
# MAGIC
# MAGIC | Env | What to set it to |
# MAGIC |-----|-------------------|
# MAGIC | `CATALOG` | the catalog holding your tables (run `SELECT current_catalog()`; often the warehouse default) |
# MAGIC | `SCHEMA` | `fraud_analytics` |
# MAGIC | `WAREHOUSE_ID` | your Serverless SQL Warehouse ID |
# MAGIC | `GENIE_SPACE_ID` | the Genie Space ID from `05` (`.../genie/rooms/<SPACE_ID>`) |
# MAGIC | `LLM_ENDPOINT` | e.g. `databricks-claude-sonnet-4-5` |
# MAGIC
# MAGIC The **Overview** screen queries `gold_fraud_claims` / `gold_fraud_by_region` in
# MAGIC `CATALOG.SCHEMA`; the **Ask Genie** screen talks to `GENIE_SPACE_ID`. If a screen is empty,
# MAGIC these two settings are the first thing to check.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Two gotchas `deploy.py` handles (do these by hand if deploying manually)
# MAGIC
# MAGIC 1. **The app runs as its own service principal with NO data access** → every query returns
# MAGIC    `HTTP 500` / `INSUFFICIENT_PERMISSIONS ... USE CATALOG`. After deploy, grant the app SP
# MAGIC    (from `databricks apps get <name>` → `service_principal_client_id`):
# MAGIC    ```bash
# MAGIC    SP=<service_principal_client_id>
# MAGIC    databricks grants update catalog <catalog> --json '{"changes":[{"principal":"'$SP'","add":["USE_CATALOG"]}]}'
# MAGIC    databricks grants update schema <catalog>.fraud_analytics --json '{"changes":[{"principal":"'$SP'","add":["USE_SCHEMA","SELECT"]}]}'
# MAGIC    databricks warehouses set-permissions <warehouse-id> --json '{"access_control_list":[{"service_principal_name":"'$SP'","permission_level":"CAN_USE"}]}'
# MAGIC    ```
# MAGIC    Also grant the SP **CAN RUN** on the Genie Space so the chat works.
# MAGIC 2. **`databricks sync` honours `.gitignore`, which ignores `frontend/dist/`** → blank page / stale
# MAGIC    UI. `deploy.py` strips that line for the sync then restores it. By hand:
# MAGIC    `grep -v 'frontend/dist' .gitignore > .gitignore.tmp && mv .gitignore.tmp .gitignore`, sync,
# MAGIC    then `git checkout .gitignore`. (A `.databricksignore` does **not** override `.gitignore` for sync.)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Try it with the sample documents
# MAGIC The repo ships documents under `docs/` you can upload in the **Ask Genie** panel, then ask the
# MAGIC questions in `docs/` (including the document-grounded ones). Uploaded files land in
# MAGIC **`raw/input/userdata`**.

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC ## Appendix · Design brief & prompts (reference only — you do **not** need these to deploy)
# MAGIC Keep these only if you want to regenerate or extend the app with **Genie Code**. To just run the
# MAGIC workshop, deploy the existing `app/` folder with the command above.

# COMMAND ----------

# MAGIC %md
# MAGIC ### Design brief (paste first so Genie Code matches the look)
# MAGIC ```
# MAGIC Build a Databricks App that looks like a clean, modern enterprise "insights" dashboard.
# MAGIC Visual style:
# MAGIC - Light theme: app background #eef1f6, white cards, 1px #e4e9f1 borders, soft shadows, 12px radius.
# MAGIC - A dark navy vertical nav rail (#14243d) on the left with icon+label items.
# MAGIC - A white top bar: bold brand wordmark, an app title, a search box, and an
# MAGIC   "Open in Unity Catalog" button in blue (#2f6df6).
# MAGIC - Primary accent blue #2f6df6; risk/fraud red #e2483b; warning amber #e8833a; Inter font.
# MAGIC - KPI tiles with a colored left border and an icon chip.
# MAGIC - All charts are lightweight inline SVG (no chart library): a line/area chart, horizontal
# MAGIC   bar charts, a grouped column chart, and a donut.
# MAGIC Two screens in the left rail: "Overview" (the dashboard) and "Ask Genie" (the chat).
# MAGIC Stack: React + Vite + TypeScript frontend, FastAPI (Python) backend, served as one app.
# MAGIC ```

# COMMAND ----------

# MAGIC %md
# MAGIC ### Backend prompts
# MAGIC ```
# MAGIC Prompt 1 — dashboard data from the Gold tables:
# MAGIC Create a FastAPI backend that queries the Gold tables via the Databricks SDK statement
# MAGIC execution API on a serverless SQL warehouse (WAREHOUSE_ID from env). Read CATALOG and SCHEMA
# MAGIC from env. Endpoints: GET /api/dashboard (KPIs: total_claims, fraud_claims, fraud_rate,
# MAGIC fraud_payout, total_payout, high_risk_claims where fraud_risk_score>=3, avg_claim; monthly
# MAGIC fraud trend from claim_month; fraud rate by region; fraud rate by policy_type; risk-score
# MAGIC distribution 0-4 split fraud vs legit); GET /api/high-risk?limit=25; GET /api/uc-link;
# MAGIC GET /api/meta. Authenticate with WorkspaceClient() in-app (SP) and a CLI profile locally.
# MAGIC
# MAGIC Prompt 2 — Genie chat + document upload to raw/input/userdata:
# MAGIC Add POST /api/chat { question, conversation_id?, doc_context? } that calls the Genie
# MAGIC Conversation API (start_conversation_and_wait first, then create_message_and_wait), reads text +
# MAGIC query.query attachments, fetches rows with get_message_query_result, and returns
# MAGIC { conversation_id, answer, sql, columns, rows }. Add POST /api/upload (multipart) that lands the
# MAGIC bytes in /Volumes/{CATALOG}/{SCHEMA}/raw/input/userdata (w.files.create_directory + upload,
# MAGIC overwrite=True), extracts text (pypdf for PDF), and returns filename, volume_path, chars, preview,
# MAGIC text. The upload path MUST be raw/input/userdata.
# MAGIC ```

# COMMAND ----------

# MAGIC %md
# MAGIC ### Frontend prompts
# MAGIC ```
# MAGIC Prompt 3 — Overview page: 4 KPI tiles (Fraud Rate red, Flagged Payout amber, High-Risk blue,
# MAGIC Avg Claim blue); an area/line chart of fraud rate over time + a fraud-vs-legit donut; horizontal
# MAGIC bars for fraud rate by region and by policy type; a grouped column chart of the risk-score
# MAGIC distribution (fraud red, legit grey); a "Highest-Risk Claims" table with a colored risk pill and
# MAGIC a Yes/No fraud column. GBP money, percentage rates. Inline SVG charts (no chart library).
# MAGIC
# MAGIC Prompt 4 — Ask Genie page: suggested questions; user (blue) and Genie (white card) bubbles with a
# MAGIC collapsible "Generated SQL" block and a result table; an input bar with paperclip upload + send.
# MAGIC On upload, POST /api/upload, show a "<file> -> raw/input/userdata" chip, and pass the returned
# MAGIC text as doc_context on later /api/chat calls. Keep conversation_id across turns.
# MAGIC
# MAGIC Prompt 5 — Package & deploy: app.yaml runs uvicorn on port 8000 with env CATALOG, SCHEMA,
# MAGIC WAREHOUSE_ID, GENIE_SPACE_ID, LLM_ENDPOINT. requirements.txt: fastapi, uvicorn, databricks-sdk,
# MAGIC python-multipart, pypdf, pydantic. vite build; FastAPI serves dist/ with a SPA fallback.
# MAGIC ```

# COMMAND ----------

# MAGIC %md
# MAGIC ### ✅ Workshop complete
# MAGIC Full path: **Setup → Data → Bronze/Silver/Gold → Genie (`05`) → Dashboard (`06`) → App (`07`, optional).**
# MAGIC All three consumption surfaces read the same Gold tables.

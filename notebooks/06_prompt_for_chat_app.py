# Databricks notebook source
# MAGIC %md
# MAGIC # 06 · Prompt Playbook — "Chat with your Data" Fraud Analytics App
# MAGIC
# MAGIC This notebook is the **prompt playbook + design brief** you paste into **Genie Code** (the
# MAGIC Databricks coding assistant) to generate a polished **Databricks App** where a user can:
# MAGIC 1. See a **fraud analytics dashboard** (KPIs, fraud-over-time, fraud by region/policy, risk-score distribution),
# MAGIC 2. **Chat with the fraud data** in natural language via the Genie Conversation API, and
# MAGIC 3. **Upload a document** (PDF / TXT / CSV / MD) — landed in **`raw/input/userdata`** — and ask questions grounded in it.
# MAGIC
# MAGIC ### A working reference implementation already ships in this repo
# MAGIC The `app/` folder contains a complete **React + FastAPI** app you can deploy as-is (see the repo
# MAGIC `README.md` and `app/README.md`). Use the prompts below either to **regenerate it with Genie Code**
# MAGIC or to understand and extend it. The design deliberately matches a clean, light,
# MAGIC enterprise "insights" look (navy left rail, white content, blue accent, KPI tiles, SVG charts).

# COMMAND ----------

# MAGIC %md
# MAGIC ## Design brief (paste this first so Genie Code matches the look)
# MAGIC
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
# MAGIC ## Prerequisites
# MAGIC - Gold tables from notebook `04` exist: `gold_fraud_claims`, `gold_fraud_by_region`.
# MAGIC - Genie Space from notebook `05` exists — copy its **Space ID** from the URL (`.../genie/rooms/<SPACE_ID>`).
# MAGIC - A **Serverless SQL Warehouse ID**.
# MAGIC - Permission to create **Databricks Apps**.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Prompt 1 · Backend — dashboard data from the Gold tables
# MAGIC
# MAGIC ```
# MAGIC Create a FastAPI backend that queries the Gold tables via the Databricks SDK statement
# MAGIC execution API on a serverless SQL warehouse (warehouse id from env WAREHOUSE_ID). Read
# MAGIC CATALOG and SCHEMA from env (default allianz_workshop / fraud_analytics). Endpoints:
# MAGIC - GET /api/dashboard  -> KPIs (total_claims, fraud_claims, fraud_rate, fraud_payout,
# MAGIC   total_payout, high_risk_claims where fraud_risk_score>=3, avg_claim), a monthly fraud
# MAGIC   trend from claim_month, fraud rate by region, fraud rate by policy_type, and a
# MAGIC   fraud_risk_score distribution (0-4) split into fraud vs legit.
# MAGIC - GET /api/high-risk?limit=25 -> highest fraud_risk_score claims with amount, region, channel.
# MAGIC - GET /api/uc-link?object=gold_fraud_claims -> a deep link into Unity Catalog.
# MAGIC - GET /api/meta -> catalog, schema, llm, stack.
# MAGIC Authenticate with WorkspaceClient() in-app (service principal) and a CLI profile locally.
# MAGIC ```

# COMMAND ----------

# MAGIC %md
# MAGIC ## Prompt 2 · Backend — Genie chat + document upload to `raw/input/userdata`
# MAGIC
# MAGIC ```
# MAGIC Add two endpoints:
# MAGIC - POST /api/chat  { question, conversation_id?, doc_context? } -> call the Genie
# MAGIC   Conversation API (w.genie). Start a conversation with start_conversation_and_wait on the
# MAGIC   first message; continue with create_message_and_wait using the returned conversation_id.
# MAGIC   Read the response attachments: text -> answer, query.query -> generated SQL, and fetch the
# MAGIC   result rows with get_message_query_result (statement_response manifest + result). If
# MAGIC   doc_context is provided, prepend it as additional context (truncate to ~6000 chars).
# MAGIC   Return { conversation_id, answer, sql, columns, rows }.
# MAGIC - POST /api/upload  (multipart file) -> IMPORTANT: land the raw bytes in the volume folder
# MAGIC   /Volumes/{CATALOG}/{SCHEMA}/raw/input/userdata using w.files.create_directory + w.files.upload
# MAGIC   (overwrite=True). Then extract text (pypdf for PDF, utf-8 decode otherwise) and return
# MAGIC   { filename, volume_path, chars, preview, text }. Sanitise the filename.
# MAGIC The upload path MUST be raw/input/userdata (not raw/input).
# MAGIC ```

# COMMAND ----------

# MAGIC %md
# MAGIC ## Prompt 3 · Frontend — the dashboard screen
# MAGIC
# MAGIC ```
# MAGIC Build a React "Overview" page using the design brief:
# MAGIC - A row of 4 KPI tiles: Fraud Rate (red), Flagged Payout (amber), High-Risk Claims (blue),
# MAGIC   Avg Claim (blue), each with an icon and a sub-label.
# MAGIC - A 2-column row: an area/line chart of fraud rate over time (red line), and a donut of
# MAGIC   fraud vs legitimate with a legend and a big fraud-rate figure.
# MAGIC - A 3-column row: horizontal bar chart of fraud rate by region, horizontal bar chart of
# MAGIC   fraud rate by policy type, and a grouped column chart of the fraud_risk_score distribution
# MAGIC   (fraud in red, legit in grey).
# MAGIC - A "Highest-Risk Claims" table with a colored risk-score pill (grey 0-1, amber 2, red 3-4)
# MAGIC   and a Yes/No fraud column. Format money as GBP (£) and rates as percentages.
# MAGIC Charts are inline SVG components (no chart library).
# MAGIC ```

# COMMAND ----------

# MAGIC %md
# MAGIC ## Prompt 4 · Frontend — the "Ask Genie" chat screen with document upload
# MAGIC
# MAGIC ```
# MAGIC Build a React "Ask Genie" chat page:
# MAGIC - A hero state with suggested questions (fraud rate, fraud by region, payout by policy type).
# MAGIC - Chat bubbles: user (blue, right) and Genie (white card, left). For a Genie answer, show the
# MAGIC   text, a collapsible "Generated SQL" block, and the result rows as a table.
# MAGIC - An input bar with a paperclip upload button and a send button.
# MAGIC - When a file is uploaded, POST it to /api/upload, show a chip "<filename> -> raw/input/userdata",
# MAGIC   and pass the returned document text as doc_context on subsequent /api/chat calls.
# MAGIC - Accept .pdf, .txt, .csv, .json, .md. Keep a conversation_id across turns.
# MAGIC ```

# COMMAND ----------

# MAGIC %md
# MAGIC ## Prompt 5 · Package & deploy
# MAGIC
# MAGIC ```
# MAGIC Add an app.yaml that runs uvicorn on port 8000 and sets env CATALOG, SCHEMA, WAREHOUSE_ID,
# MAGIC GENIE_SPACE_ID, LLM_ENDPOINT. requirements.txt: fastapi, uvicorn, databricks-sdk,
# MAGIC python-multipart, pypdf, pydantic. Build the frontend (vite build) and have FastAPI serve the
# MAGIC dist/ as static files with a SPA fallback. Then give me the databricks CLI commands to sync
# MAGIC and deploy the app, and grant the app service principal access.
# MAGIC ```
# MAGIC
# MAGIC ### ⚠️ Two gotchas the deploy script (`app/deploy.py`) handles for you
# MAGIC These were hit during the real end-to-end deployment — bake them into any regenerated app:
# MAGIC
# MAGIC 1. **The app runs as its own service principal, which has NO data access by default** →
# MAGIC    every query returns `HTTP 500` with `INSUFFICIENT_PERMISSIONS ... USE CATALOG`. After
# MAGIC    deploy, grant the app SP (from `databricks apps get <name>` → `service_principal_client_id`):
# MAGIC    ```bash
# MAGIC    SP=<service_principal_client_id>
# MAGIC    databricks grants update catalog <catalog> --json '{"changes":[{"principal":"'$SP'","add":["USE_CATALOG"]}]}'
# MAGIC    databricks grants update schema <catalog>.<schema> --json '{"changes":[{"principal":"'$SP'","add":["USE_SCHEMA","SELECT"]}]}'
# MAGIC    databricks warehouses set-permissions <warehouse-id> --json '{"access_control_list":[{"service_principal_name":"'$SP'","permission_level":"CAN_USE"}]}'
# MAGIC    ```
# MAGIC    Also give the SP **CAN RUN** on the Genie space so the chat works.
# MAGIC 2. **`databricks sync` honours `.gitignore`, which ignores `frontend/dist/`** → the app starts
# MAGIC    with no frontend (blank page) or a stale UI. `deploy.py` temporarily strips the `frontend/dist`
# MAGIC    line from `.gitignore` for the sync, then restores it. Doing it by hand:
# MAGIC    `grep -v 'frontend/dist' .gitignore > .gitignore.tmp && mv .gitignore.tmp .gitignore`, sync,
# MAGIC    then `git checkout .gitignore`. A `.databricksignore` does NOT override `.gitignore` for sync.
# MAGIC
# MAGIC ### One-command deploy (recommended)
# MAGIC ```bash
# MAGIC cd app
# MAGIC python deploy.py --profile <profile> --warehouse-id <id> --app-name fraud-analytics
# MAGIC ```
# MAGIC This resolves the catalog (with `allianz_workshop`→managed fallback), creates the Genie space
# MAGIC with verbose instructions, builds+syncs+deploys, applies all grants, and prints the URL.
# MAGIC See `app/DEPLOY.md` for the full explanation and the manual sequence.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Try it with the sample documents
# MAGIC The repo ships two documents under `docs/` you can upload in the "Ask Genie" panel:
# MAGIC - **`sample_fraud_event_report.md`** — a verbose SIU fraud investigation tied to the dataset fields.
# MAGIC - **`sample_eu_compliance_policy.md`** — an EU/GDPR compliance framework for fraud analytics.
# MAGIC
# MAGIC Then ask questions from **`docs/genie_sample_questions.md`** (10+ questions), including the
# MAGIC document-grounded ones at the end. Uploaded files land in **`raw/input/userdata`**.

# COMMAND ----------

# MAGIC %md
# MAGIC ### ✅ Workshop complete
# MAGIC Full path: **Setup → Data → Bronze → Silver/Gold (Visual Data Prep) → Genie → App.**
# MAGIC The `app/` folder is a working reference you can deploy directly.

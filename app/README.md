# Fraud Analytics App (React + FastAPI)

A "chat with your data" Databricks App for insurance fraud analytics. Two screens:

- **Overview** — KPI tiles (fraud rate, flagged payout, high-risk count, avg claim), fraud-rate
  trend, fraud-vs-legit donut, fraud rate by region and policy type, risk-score distribution, and
  a highest-risk claims table.
- **Ask Genie** — natural-language chat over the fraud data via the Genie Conversation API, plus
  document upload. **Uploaded files land in the volume folder `raw/input/userdata`.**

The look matches a clean, light enterprise "insights" dashboard: navy left rail, white cards,
blue accent, Inter font, and lightweight inline-SVG charts (no chart library).

## Layout

```
app/
├── app.py               # FastAPI entry: dashboard, high-risk, chat, upload, static SPA
├── app.yaml             # Databricks App run command + env
├── requirements.txt
├── server/
│   ├── config.py        # env + WorkspaceClient (SP in-app, CLI profile locally)
│   ├── db.py            # SQL warehouse + LLM helpers
│   ├── backend.py       # dashboard + high-risk queries over the Gold tables
│   └── genie.py         # Genie Conversation API + upload to raw/input/userdata
└── frontend/            # React + Vite + TS; built to frontend/dist and served by FastAPI
```

## Configure

Set these in `app.yaml` (or as env vars) before deploying:

| Env | Meaning |
|-----|---------|
| `CATALOG` | `allianz_workshop` (or `default`) |
| `SCHEMA` | `fraud_analytics` |
| `WAREHOUSE_ID` | your Serverless SQL warehouse id |
| `GENIE_SPACE_ID` | Genie space id from notebook `05` |
| `LLM_ENDPOINT` | e.g. `databricks-claude-sonnet-4-5` |

## Run locally

```bash
# backend (uses your Databricks CLI profile)
pip install -r requirements.txt
export DATABRICKS_CONFIG_PROFILE=<your-profile>
export CATALOG=allianz_workshop SCHEMA=fraud_analytics WAREHOUSE_ID=<id> GENIE_SPACE_ID=<id>
uvicorn app:app --reload --port 8000

# frontend (in another shell) — proxies /api to :8000
cd frontend && npm install && npm run dev
```

## Deploy to Databricks Apps

```bash
cd app
(cd frontend && npm install && npm run build)   # produces frontend/dist
databricks apps create fraud-analytics --profile <profile>
databricks sync . /Workspace/Users/<you>/fraud-analytics-app --profile <profile>
databricks apps deploy fraud-analytics \
  --source-code-path /Workspace/Users/<you>/fraud-analytics-app --profile <profile>
```

Grant the app's service principal `CAN QUERY` on the SQL warehouse and `CAN RUN` on the Genie
space, and `SELECT` on the Gold tables. Then open the app URL printed by the deploy command.

## Sample documents

Upload one of the files in the repo `docs/` folder in the **Ask Genie** panel, then ask the
document-grounded questions in `docs/genie_sample_questions.md`.

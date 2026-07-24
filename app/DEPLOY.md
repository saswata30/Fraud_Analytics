# Deploying the Fraud Analytics app — the complete, gotcha-free path

`deploy.py` automates all of this. This doc explains what it does and the two mistakes that
otherwise cause a blank page or a `500 Internal Server Error`.

## One command

```bash
cd app
python deploy.py \
  --profile   <your-databricks-cli-profile> \
  --warehouse-id <serverless-sql-warehouse-id> \
  --app-name  fraud-analytics
# optional: --catalog allianz_workshop --schema fraud_analytics --genie-space-id <existing>
```

## What it does (and why)

1. **Resolve the catalog.** It tries `CREATE CATALOG allianz_workshop`. On many FEVM metastores
   this fails with *"Metastore storage root URL does not exist / Default Storage is enabled"* — in
   that case it automatically falls back to an existing managed catalog. (You can force one with
   `--catalog`.)
2. **Create the Genie space** over `gold_fraud_claims` + `gold_fraud_by_region` with verbose,
   demo-grade instructions, and return its `space_id`.
3. **Write `app.yaml`** with the resolved `CATALOG`, `SCHEMA`, `WAREHOUSE_ID`, `GENIE_SPACE_ID`.
4. **Create the app**, build the frontend, **sync (including `frontend/dist`)**, and deploy.
5. **Grant the app service principal** least-privilege access.
6. **Print the app URL.**

## Gotcha 1 — the app SP has no data access (causes HTTP 500)

A Databricks App runs as its **own service principal**, not as you. Freshly created, it can't read
your catalog, so every `/api/dashboard` call fails with:

```
[INSUFFICIENT_PERMISSIONS] User does not have USE CATALOG on Catalog '...'
```

You must grant the app SP (get it from `databricks apps get <name>` → `service_principal_client_id`):

```bash
SP=<service_principal_client_id>
databricks grants update catalog <catalog> --profile <p> \
  --json '{"changes":[{"principal":"'$SP'","add":["USE_CATALOG"]}]}'
databricks grants update schema <catalog>.<schema> --profile <p> \
  --json '{"changes":[{"principal":"'$SP'","add":["USE_SCHEMA","SELECT"]}]}'
databricks warehouses set-permissions <warehouse-id> --profile <p> \
  --json '{"access_control_list":[{"service_principal_name":"'$SP'","permission_level":"CAN_USE"}]}'
```

Also give the SP **CAN RUN** on the Genie space (Genie UI → Share, or the permissions API) so the
chat works.

## Gotcha 2 — no frontend shows up (blank page / 404)

`databricks sync` honours `.gitignore`. The repo's `app/.gitignore` ignores `frontend/dist/` (correct
for git — we don't commit build output). But the **deployed** app needs `dist/` because there is no
Node build step in the Apps runtime. `deploy.py` handles this; if you deploy by hand, make sure
`frontend/dist` is uploaded (a `.databricksignore` that does **not** exclude `dist`, or a sync from a
copy where `dist` isn't gitignored).

Verify after sync:
```bash
databricks workspace list /Workspace/Users/<you>/fraud-analytics-app/frontend/dist/assets --profile <p>
```

## Manual sequence (if you prefer)

```bash
cd app
(cd frontend && npm install && npm run build)
databricks apps create fraud-analytics --profile <p>
databricks sync . /Workspace/Users/<you>/fraud-analytics-app --profile <p>   # ensure dist included
databricks apps deploy fraud-analytics \
  --source-code-path /Workspace/Users/<you>/fraud-analytics-app --profile <p>
# then apply the grants from Gotcha 1
```

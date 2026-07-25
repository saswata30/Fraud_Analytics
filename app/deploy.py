#!/usr/bin/env python3
"""One-shot deployer for the Fraud Analytics app on a Databricks (FEVM) workspace.

This codifies every step — and every permission fix — needed to get the app running,
so you don't rediscover them by hitting 500s in the UI:

  1. Resolve the catalog: try to create `allianz_workshop`; fall back to an existing
     managed catalog if the metastore uses Default Storage (common on FEVM).
  2. Create the Genie space over the Gold tables with verbose, demo-grade instructions.
  3. Create the Databricks App (compute provision).
  4. Build the frontend, sync source INCLUDING frontend/dist, and deploy.
  5. GRANT the app's service principal what it needs — this is the step people miss:
       - USE CATALOG on the catalog
       - USE SCHEMA + SELECT on the schema
       - CAN_USE on the SQL warehouse
       - CAN_RUN on the Genie space
  6. Print the app URL.

Usage:
  python deploy.py --profile <cli-profile> --warehouse-id <id> \
      [--catalog allianz_workshop] [--schema fraud_analytics] \
      [--app-name fraud-analytics] [--genie-space-id <existing>]

Requires: databricks CLI on PATH, npm on PATH, databricks-sdk installed.
"""
import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

from databricks.sdk import WorkspaceClient

HERE = Path(__file__).resolve().parent


def sh(*args, check=True, capture=False):
    print("  $ " + " ".join(args))
    return subprocess.run(args, check=check,
                          capture_output=capture, text=True)


def resolve_catalog(w, preferred, warehouse_id):
    """Try preferred catalog; fall back to an existing managed catalog on failure."""
    from databricks.sdk.service.sql import StatementState

    def run(q):
        r = w.statement_execution.execute_statement(
            warehouse_id=warehouse_id, statement=q, wait_timeout="30s")
        while r.status and r.status.state in (StatementState.PENDING, StatementState.RUNNING):
            time.sleep(1); r = w.statement_execution.get_statement(r.statement_id)
        if r.status and r.status.state != StatementState.SUCCEEDED:
            raise RuntimeError(r.status.error.message if r.status.error else "sql error")
        return r

    try:
        run(f"CREATE CATALOG IF NOT EXISTS {preferred}")
        print(f"  using catalog: {preferred}")
        return preferred
    except Exception as e:
        print(f"  ! could not create '{preferred}': {e}")
        # fall back to the first managed catalog we can write to
        for c in w.catalogs.list():
            if c.catalog_type and "MANAGED" in str(c.catalog_type):
                print(f"  falling back to existing managed catalog: {c.name}")
                return c.name
        raise SystemExit("No usable catalog found; create one in the UI and pass --catalog.")


def create_genie_space(profile, warehouse_id, catalog, schema):
    """Create the Genie space with verbose instructions. Returns the space_id."""
    fq = f"{catalog}.{schema}"
    instructions = (
        "You are the analytics assistant for an insurance fraud investigation team at Allianz. "
        "Answer in clear, professional British English suitable for a customer demo.\n\n"
        "DATA: Claims across Auto, Home, Health, Travel, Life, Commercial. Two Gold tables: "
        "gold_fraud_claims (row-level fact) and gold_fraud_by_region (pre-aggregated by region and "
        "policy_type). is_fraud=1 is confirmed fraud, 0 legitimate. claim_amount is GBP (format with £). "
        "fraud_risk_score is 0-4 (sum of high_value, fast_report, new_customer, low_credit flags). "
        "report_lag_days is days from incident to report.\n\n"
        "DEFINITIONS: Fraud rate = SUM(is_fraud)/COUNT(*), shown as a percentage. High-risk = "
        "fraud_risk_score>=3. High-value = claim_amount>20000. Fast-reported = report_lag_days<=2. "
        "Fraudulent payout = SUM(claim_amount) WHERE is_fraud=1.\n\n"
        "HOW TO ANSWER: Lead with the number then the breakdown. Prefer gold_fraud_by_region for "
        "region/policy roll-ups; gold_fraud_claims for detail, channel, and time trends. When the user "
        "references an uploaded document, combine it with the data.\n\n"
        "GUARDRAILS: Only answer questions about this dataset. fraud_risk_score is a triage indicator "
        "for human review, not an automated approve/deny decision. Do not invent columns or values."
    )

    inner = {
        "version": 2,
        "data_sources": {"tables": [
            {"identifier": f"{fq}.gold_fraud_by_region"},
            {"identifier": f"{fq}.gold_fraud_claims"},
        ]},
        "instructions": {
            "text_instructions": [{"id": "000000000000000000000000000000ff", "content": [instructions]}],
            "example_question_sqls": sorted([
                {"id": "00000000000000000000000000000001",
                 "question": ["Overall fraud rate"],
                 "sql": [f"SELECT SUM(is_fraud)/COUNT(*) AS fraud_rate FROM {fq}.gold_fraud_claims"]},
                {"id": "00000000000000000000000000000002",
                 "question": ["Fraud rate by region"],
                 "sql": [f"SELECT region, SUM(is_fraud)/COUNT(*) AS fraud_rate, COUNT(*) AS claims "
                         f"FROM {fq}.gold_fraud_claims GROUP BY region ORDER BY fraud_rate DESC"]},
                {"id": "00000000000000000000000000000003",
                 "question": ["Fraudulent payout by policy type"],
                 "sql": [f"SELECT policy_type, SUM(claim_amount) AS fraud_payout FROM {fq}.gold_fraud_claims "
                         f"WHERE is_fraud=1 GROUP BY policy_type ORDER BY fraud_payout DESC"]},
            ], key=lambda x: x["id"]),
        },
    }
    payload = {
        "title": "Insurance Fraud Analytics",
        "description": "Ask questions about insurance claims and fraud for the Allianz workshop.",
        "warehouse_id": warehouse_id,
        "serialized_space": json.dumps(inner),
    }
    tmp = HERE / ".genie_create.json"
    tmp.write_text(json.dumps(payload))
    out = sh("databricks", "api", "post", "/api/2.0/genie/spaces",
             "--profile", profile, "--json", f"@{tmp}", capture=True)
    tmp.unlink(missing_ok=True)
    space_id = json.loads(out.stdout).get("space_id")
    print(f"  Genie space: {space_id}")
    return space_id


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", required=True)
    ap.add_argument("--warehouse-id", required=True)
    ap.add_argument("--catalog", default="allianz_workshop")
    ap.add_argument("--schema", default="fraud_analytics")
    ap.add_argument("--app-name", default="fraud-analytics")
    ap.add_argument("--genie-space-id", default="")
    ap.add_argument("--workspace-user", default="", help="e.g. you@company.com (defaults to current user)")
    args = ap.parse_args()

    w = WorkspaceClient(profile=args.profile)
    user = args.workspace_user or w.current_user.me().user_name
    src_path = f"/Workspace/Users/{user}/{args.app_name}-app"

    print("[1/6] Resolve catalog")
    catalog = resolve_catalog(w, args.catalog, args.warehouse_id)

    print("[2/6] Genie space")
    genie_id = args.genie_space_id or create_genie_space(
        args.profile, args.warehouse_id, catalog, args.schema)

    print("[3/6] Write app.yaml env + create app")
    (HERE / "app.yaml").write_text(f"""command:
  - "python"
  - "-m"
  - "uvicorn"
  - "app:app"
  - "--host"
  - "0.0.0.0"
  - "--port"
  - "8000"

env:
  - name: CATALOG
    value: "{catalog}"
  - name: SCHEMA
    value: "{args.schema}"
  - name: WAREHOUSE_ID
    value: "{args.warehouse_id}"
  - name: GENIE_SPACE_ID
    value: "{genie_id}"
  - name: LLM_ENDPOINT
    value: "databricks-claude-sonnet-4-5"
""")
    sh("databricks", "apps", "create", args.app_name, "--profile", args.profile, check=False)

    print("[4/6] Build frontend + sync (INCLUDING dist) + deploy")
    sh("npm", "--prefix", str(HERE / "frontend"), "install")
    sh("npm", "--prefix", str(HERE / "frontend"), "run", "build")
    # `databricks sync` honours .gitignore, which lists frontend/dist/ (correct for git —
    # we don't commit build output). But the deployed app NEEDS dist (there is no Node build
    # step in the Apps runtime). Temporarily drop the dist exclusion from .gitignore for the
    # sync, then restore it, so the built frontend is uploaded but git stays clean.
    # Prune any previously-deployed hashed bundles so a stale index-*.js/css can't linger
    # alongside the new one (Vite emits content-hashed filenames, so sync only ADDS).
    assets_dir = f"{src_path}/frontend/dist/assets"
    local_assets = {p.name for p in (HERE / "frontend" / "dist" / "assets").glob("*")}
    listing = sh("databricks", "workspace", "list", assets_dir, "--output", "json",
                 "--profile", args.profile, check=False, capture=True).stdout
    try:
        for obj in json.loads(listing or "[]"):
            name = obj.get("path", "").rsplit("/", 1)[-1]
            if name and name not in local_assets:
                sh("databricks", "workspace", "delete", f"{assets_dir}/{name}",
                   "--profile", args.profile, check=False)
    except (json.JSONDecodeError, TypeError):
        pass

    gitignore = HERE / ".gitignore"
    original = gitignore.read_text() if gitignore.exists() else None
    try:
        if original is not None:
            kept = [ln for ln in original.splitlines() if "frontend/dist" not in ln]
            gitignore.write_text("\n".join(kept) + "\n")
        sh("databricks", "sync", str(HERE), src_path, "--profile", args.profile, check=False)
    finally:
        if original is not None:
            gitignore.write_text(original)
    sh("databricks", "apps", "deploy", args.app_name,
       "--source-code-path", src_path, "--profile", args.profile)

    print("[5/6] Grant the app service principal least-privilege access")
    app = json.loads(sh("databricks", "apps", "get", args.app_name,
                        "--profile", args.profile, capture=True).stdout)
    sp = app.get("service_principal_client_id")
    print(f"  app SP: {sp}")
    sh("databricks", "grants", "update", "catalog", catalog, "--profile", args.profile,
       "--json", json.dumps({"changes": [{"principal": sp, "add": ["USE_CATALOG"]}]}))
    sh("databricks", "grants", "update", "schema", f"{catalog}.{args.schema}", "--profile", args.profile,
       "--json", json.dumps({"changes": [{"principal": sp, "add": ["USE_SCHEMA", "SELECT"]}]}))
    # READ/WRITE on the `raw` volume so document upload (raw/input/userdata) works — without
    # this the app returns 500 on /api/upload even though dashboard queries succeed.
    sh("databricks", "grants", "update", "volume", f"{catalog}.{args.schema}.raw", "--profile", args.profile,
       "--json", json.dumps({"changes": [{"principal": sp, "add": ["READ_VOLUME", "WRITE_VOLUME"]}]}), check=False)
    sh("databricks", "warehouses", "set-permissions", args.warehouse_id, "--profile", args.profile,
       "--json", json.dumps({"access_control_list": [
           {"service_principal_name": sp, "permission_level": "CAN_USE"}]}))
    # Genie space CAN_RUN so the app SP can drive the Conversation API
    sh("databricks", "api", "patch", f"/api/2.0/permissions/genie/{genie_id}",
       "--profile", args.profile, "--json", json.dumps({"access_control_list": [
           {"service_principal_name": sp, "permission_level": "CAN_RUN"}]}), check=False)

    print("[6/6] Done")
    app = json.loads(sh("databricks", "apps", "get", args.app_name,
                        "--profile", args.profile, capture=True).stdout)
    print(f"\n  App URL: {app.get('url')}")
    print(f"  Genie space: {genie_id}")
    print(f"  Data: {catalog}.{args.schema}")


if __name__ == "__main__":
    main()

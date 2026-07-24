import os
from functools import lru_cache

from databricks.sdk import WorkspaceClient

# ---- environment (wired via app.yaml in-app, or shell/.env locally) ----
# CATALOG is normally set explicitly by deploy.py / app.yaml. If it is unset — or the
# configured catalog doesn't actually contain the fraud_analytics.gold_fraud_claims table
# (e.g. the notebooks resolved to `main` or `hive_metastore` in a lab workspace) — the app
# falls back through these candidates so it keeps working instead of returning 500s.
CATALOG = os.environ.get("CATALOG", "allianz_workshop")
SCHEMA = os.environ.get("SCHEMA", "fraud_analytics")
WAREHOUSE_ID = os.environ.get("WAREHOUSE_ID", "")
LLM = os.environ.get("LLM_ENDPOINT", "databricks-claude-sonnet-4-5")
GENIE_SPACE_ID = os.environ.get("GENIE_SPACE_ID", "")

# Candidate catalogs to probe (in order) when the configured one has no gold table.
_CATALOG_CANDIDATES = [CATALOG, "allianz_lab", "allianz_workshop", "main", "hive_metastore"]

# Volume folder where user-uploaded documents are landed for analysis.
VOLUME = os.environ.get("VOLUME", "raw")
USERDATA_SUBDIR = os.environ.get("USERDATA_SUBDIR", "input/userdata")

FQ = f"{CATALOG}.{SCHEMA}"  # fully-qualified schema prefix (may be re-resolved lazily)
USERDATA_PATH = f"/Volumes/{CATALOG}/{SCHEMA}/{VOLUME}/{USERDATA_SUBDIR}"

IS_DATABRICKS_APP = bool(os.environ.get("DATABRICKS_APP_NAME"))


@lru_cache(maxsize=1)
def get_workspace_client() -> WorkspaceClient:
    """WorkspaceClient. In-app: injected SP creds. Local: CLI profile."""
    if IS_DATABRICKS_APP:
        return WorkspaceClient()
    profile = os.environ.get("DATABRICKS_CONFIG_PROFILE", "DEFAULT")
    return WorkspaceClient(profile=profile)


@lru_cache(maxsize=1)
def get_openai_client():
    """OpenAI-compatible client backed by the workspace serving endpoints."""
    return get_workspace_client().serving_endpoints.get_open_ai_client()


def workspace_host() -> str:
    try:
        return get_workspace_client().config.host.rstrip("/")
    except Exception:
        return os.environ.get("DATABRICKS_HOST", "").rstrip("/")


_resolved = False


def resolve_catalog(run_sql) -> str:
    """Ensure CATALOG points at a catalog that actually has SCHEMA.gold_fraud_claims.

    Called once (lazily) by the backend before its first query. `run_sql` is the SQL
    helper from server.db (passed in to avoid a circular import). Idempotent.
    """
    global CATALOG, FQ, USERDATA_PATH, _resolved
    if _resolved:
        return CATALOG
    seen = set()
    for cand in _CATALOG_CANDIDATES:
        if not cand or cand in seen:
            continue
        seen.add(cand)
        try:
            run_sql(f"SELECT 1 FROM {cand}.{SCHEMA}.gold_fraud_claims LIMIT 1")
            CATALOG = cand
            FQ = f"{CATALOG}.{SCHEMA}"
            USERDATA_PATH = f"/Volumes/{CATALOG}/{SCHEMA}/{VOLUME}/{USERDATA_SUBDIR}"
            _resolved = True
            return CATALOG
        except Exception:
            continue
    # nothing matched — keep the configured value; the error will surface normally
    _resolved = True
    return CATALOG

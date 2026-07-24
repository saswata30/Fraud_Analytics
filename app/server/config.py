import os
from functools import lru_cache

from databricks.sdk import WorkspaceClient

# ---- environment (wired via app.yaml in-app, or shell/.env locally) ----
CATALOG = os.environ.get("CATALOG", "allianz_workshop")
SCHEMA = os.environ.get("SCHEMA", "fraud_analytics")
WAREHOUSE_ID = os.environ.get("WAREHOUSE_ID", "")
LLM = os.environ.get("LLM_ENDPOINT", "databricks-claude-sonnet-4-5")
GENIE_SPACE_ID = os.environ.get("GENIE_SPACE_ID", "")

# Volume folder where user-uploaded documents are landed for analysis.
VOLUME = os.environ.get("VOLUME", "raw")
USERDATA_SUBDIR = os.environ.get("USERDATA_SUBDIR", "input/userdata")

FQ = f"{CATALOG}.{SCHEMA}"  # fully-qualified schema prefix
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

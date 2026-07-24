"""Thin SQL + LLM helpers shared by the app backend."""
from __future__ import annotations

import time
from typing import Any

from databricks.sdk.service.sql import StatementParameterListItem, StatementState

from server.config import LLM, WAREHOUSE_ID, get_openai_client, get_workspace_client


# ------------------------------ SQL ------------------------------
def sql(query: str, params: list | None = None) -> list[dict[str, Any]]:
    """Run a query on the serverless SQL warehouse, return list-of-dicts."""
    w = get_workspace_client()
    kwargs: dict[str, Any] = dict(
        warehouse_id=WAREHOUSE_ID, statement=query, wait_timeout="50s"
    )
    if params:
        kwargs["parameters"] = [
            StatementParameterListItem(name=p["name"], value=p["value"]) for p in params
        ]
    resp = w.statement_execution.execute_statement(**kwargs)

    while resp.status and resp.status.state in (
        StatementState.PENDING,
        StatementState.RUNNING,
    ):
        time.sleep(1)
        resp = w.statement_execution.get_statement(resp.statement_id)

    if resp.status and resp.status.state != StatementState.SUCCEEDED:
        msg = resp.status.error.message if resp.status.error else "unknown"
        raise RuntimeError(f"SQL failed: {msg}\n---\n{query[:1500]}")

    if not resp.manifest or not resp.manifest.schema or not resp.result:
        return []
    cols = [c.name for c in resp.manifest.schema.columns]
    rows = resp.result.data_array or []
    return [dict(zip(cols, r)) for r in rows]


def sql_scalar(query: str, params: list | None = None):
    rows = sql(query, params)
    if not rows:
        return None
    return next(iter(rows[0].values()))


# ------------------------------ LLM ------------------------------
def llm(system: str, user: str, *, model: str | None = None,
        temperature: float = 0.2, max_tokens: int = 1500) -> str:
    client = get_openai_client()
    resp = client.chat.completions.create(
        model=model or LLM,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return resp.choices[0].message.content or ""


__all__ = ["sql", "sql_scalar", "llm"]

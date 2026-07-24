"""Read-side business logic: serves fraud analytics from the Gold Delta tables."""
from __future__ import annotations

from server.config import FQ, LLM, workspace_host
from server.db import sql, sql_scalar


# ------------------------------ Dashboard: KPIs + trends ------------------------------
def dashboard() -> dict:
    """Top KPIs, fraud-over-time trend, region/policy breakdown, risk distribution."""
    kpi = sql(
        f"""
        SELECT
          COUNT(*)                              AS total_claims,
          SUM(is_fraud)                         AS fraud_claims,
          SUM(is_fraud) / COUNT(*)              AS fraud_rate,
          SUM(CASE WHEN is_fraud=1 THEN claim_amount ELSE 0 END) AS fraud_payout,
          SUM(claim_amount)                     AS total_payout,
          SUM(CASE WHEN fraud_risk_score >= 3 THEN 1 ELSE 0 END) AS high_risk_claims,
          AVG(claim_amount)                     AS avg_claim
        FROM {FQ}.gold_fraud_claims
        """
    )
    kpi = kpi[0] if kpi else {}

    # Fraud trend over time (by claim month)
    trend = sql(
        f"""
        SELECT date_format(claim_month, 'yyyy-MM') AS month,
               COUNT(*)                 AS claims,
               SUM(is_fraud)            AS fraud_claims,
               SUM(is_fraud)/COUNT(*)   AS fraud_rate,
               SUM(CASE WHEN is_fraud=1 THEN claim_amount ELSE 0 END) AS fraud_payout
        FROM {FQ}.gold_fraud_claims
        WHERE claim_month IS NOT NULL
        GROUP BY claim_month
        ORDER BY claim_month
        """
    )

    # Fraud by region
    by_region = sql(
        f"""
        SELECT region,
               COUNT(*)               AS claims,
               SUM(is_fraud)          AS fraud_claims,
               SUM(is_fraud)/COUNT(*) AS fraud_rate,
               SUM(CASE WHEN is_fraud=1 THEN claim_amount ELSE 0 END) AS fraud_payout
        FROM {FQ}.gold_fraud_claims
        GROUP BY region
        ORDER BY fraud_rate DESC
        """
    )

    # Fraud by policy type
    by_policy = sql(
        f"""
        SELECT policy_type,
               COUNT(*)               AS claims,
               SUM(is_fraud)          AS fraud_claims,
               SUM(is_fraud)/COUNT(*) AS fraud_rate
        FROM {FQ}.gold_fraud_claims
        GROUP BY policy_type
        ORDER BY fraud_rate DESC
        """
    )

    # Risk-score distribution (0-4), split fraud vs legit
    risk_dist = sql(
        f"""
        SELECT fraud_risk_score AS score,
               COUNT(*)                            AS total,
               SUM(is_fraud)                       AS fraud,
               COUNT(*) - SUM(is_fraud)            AS legit
        FROM {FQ}.gold_fraud_claims
        GROUP BY fraud_risk_score
        ORDER BY fraud_risk_score
        """
    )

    for coll, numcols in [
        (trend, ["claims", "fraud_claims", "fraud_rate", "fraud_payout"]),
        (by_region, ["claims", "fraud_claims", "fraud_rate", "fraud_payout"]),
        (by_policy, ["claims", "fraud_claims", "fraud_rate"]),
        (risk_dist, ["score", "total", "fraud", "legit"]),
    ]:
        for r in coll:
            for c in numcols:
                r[c] = float(r.get(c) or 0)

    return {
        "kpi": {k: float(v or 0) for k, v in kpi.items()},
        "trend": trend,
        "by_region": by_region,
        "by_policy": by_policy,
        "risk_dist": risk_dist,
    }


# ------------------------------ High-risk claims table ------------------------------
def high_risk_claims(limit: int = 25) -> list[dict]:
    rows = sql(
        f"""
        SELECT claim_id, policyholder_id, policy_type, claim_type, region, channel,
               claim_date, claim_amount, report_lag_days, fraud_risk_score,
               claim_status, is_fraud
        FROM {FQ}.gold_fraud_claims
        ORDER BY fraud_risk_score DESC, claim_amount DESC
        LIMIT {int(limit)}
        """
    )
    for r in rows:
        r["claim_amount"] = float(r.get("claim_amount") or 0)
        r["fraud_risk_score"] = int(r.get("fraud_risk_score") or 0)
        r["report_lag_days"] = int(r.get("report_lag_days") or 0)
        r["is_fraud"] = int(r.get("is_fraud") or 0)
    return rows


# ------------------------------ Unity Catalog deep link ------------------------------
def uc_link(obj: str = "") -> dict:
    cat, sch = FQ.split(".")
    host = workspace_host()
    url = f"{host}/explore/data/{cat}/{sch}/{obj}" if obj else f"{host}/explore/data/{cat}/{sch}"
    return {"url": url}


def meta() -> dict:
    cat, sch = FQ.split(".")
    return {
        "catalog": cat,
        "schema": sch,
        "llm": LLM,
        "stack": ["Unity Catalog", "Genie", "Delta Lake", "Claude Sonnet 4.5", "Databricks Apps"],
    }

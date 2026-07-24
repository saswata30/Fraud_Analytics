# Databricks notebook source
# MAGIC %md
# MAGIC # 02 · Generate Synthetic Data — Insurance Fraud
# MAGIC
# MAGIC Generates a realistic, **fraud-labelled insurance claims** dataset for the workshop and writes it to the
# MAGIC `raw/input` volume as both **CSV** and **Parquet**.
# MAGIC
# MAGIC The design follows common Databricks synthetic-data patterns (Faker + NumPy, deterministic seed, an
# MAGIC injected fraud signal so the label is *learnable*):
# MAGIC
# MAGIC | File | Rows | Grain | Purpose |
# MAGIC |------|------|-------|---------|
# MAGIC | `policyholders.*`  | 1,500 | one row per customer | dimension |
# MAGIC | `claims.*`         | 5,000+ | one row per claim   | fact (fraud label lives here) |
# MAGIC
# MAGIC > **How to run:** Run `01_setup` first, then `Run all` here. Each activity is broken into its own cell.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 1 · Install dependencies

# COMMAND ----------

# MAGIC %pip install faker==25.2.0
# MAGIC %restart_python

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 2 · Configuration
# MAGIC Keep these in sync with `01_setup`. If `allianz_workshop` was not created, change `CATALOG` to `default`.

# COMMAND ----------

CATALOG       = "allianz_workshop"   # or "default" if catalog creation was not permitted
SCHEMA        = "fraud_analytics"
VOLUME        = "raw"
VOLUME_SUBDIR = "input"

INPUT_PATH = f"/Volumes/{CATALOG}/{SCHEMA}/{VOLUME}/{VOLUME_SUBDIR}"

N_POLICYHOLDERS = 1_500
N_CLAIMS        = 5_000
SEED            = 42

print(f"Writing files to: {INPUT_PATH}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 3 · Imports & deterministic seed

# COMMAND ----------

import numpy as np
import pandas as pd
from faker import Faker
from datetime import datetime, timedelta

fake = Faker("en_GB")
Faker.seed(SEED)
np.random.seed(SEED)
rng = np.random.default_rng(SEED)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 4 · Reference data (insurance domain)
# MAGIC Lookup values used to build realistic categorical columns.

# COMMAND ----------

REGIONS       = ["London", "South East", "North West", "Scotland", "Wales",
                 "Midlands", "South West", "North East", "Yorkshire", "Northern Ireland"]
POLICY_TYPES  = ["Auto", "Home", "Health", "Travel", "Life", "Commercial"]
CLAIM_TYPES   = {
    "Auto":       ["Collision", "Theft", "Windscreen", "Third Party", "Fire"],
    "Home":       ["Flood", "Burglary", "Fire", "Storm", "Accidental Damage"],
    "Health":     ["Hospitalisation", "Outpatient", "Dental", "Optical"],
    "Travel":     ["Cancellation", "Medical", "Lost Luggage", "Delay"],
    "Life":       ["Death Benefit", "Critical Illness"],
    "Commercial": ["Liability", "Property Damage", "Business Interruption"],
}
CHANNELS      = ["Branch", "Online", "Broker", "Call Center", "Mobile App"]
CLAIM_STATUS  = ["Approved", "Rejected", "Pending", "Under Review"]
GENDERS       = ["Male", "Female", "Other"]

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 5 · Generate the `policyholders` dimension

# COMMAND ----------

policyholder_ids = [f"PH{100000 + i}" for i in range(N_POLICYHOLDERS)]

policyholders = pd.DataFrame({
    "policyholder_id": policyholder_ids,
    "full_name":       [fake.name() for _ in range(N_POLICYHOLDERS)],
    "gender":          rng.choice(GENDERS, N_POLICYHOLDERS, p=[0.48, 0.48, 0.04]),
    "date_of_birth":   [fake.date_of_birth(minimum_age=18, maximum_age=85) for _ in range(N_POLICYHOLDERS)],
    "region":          rng.choice(REGIONS, N_POLICYHOLDERS),
    "email":           [fake.email() for _ in range(N_POLICYHOLDERS)],
    "phone":           [fake.phone_number() for _ in range(N_POLICYHOLDERS)],
    "customer_since":  [fake.date_between(start_date="-10y", end_date="-1y") for _ in range(N_POLICYHOLDERS)],
    "credit_score":    rng.integers(300, 850, N_POLICYHOLDERS),
})

print(f"policyholders: {policyholders.shape}")
policyholders.head()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 6 · Generate the `claims` fact table
# MAGIC We inject a realistic fraud signal: fraudulent claims skew toward **higher amounts**, **shorter tenure**,
# MAGIC **specific channels**, and **fast filing after policy start**. This makes the label learnable in Genie/ML later.

# COMMAND ----------

FRAUD_RATE = 0.07  # ~7% of claims are fraudulent — typical for insurance datasets

rows = []
start_window = datetime(2023, 1, 1)

for i in range(N_CLAIMS):
    ph        = policyholders.iloc[rng.integers(0, N_POLICYHOLDERS)]
    ptype     = rng.choice(POLICY_TYPES)
    ctype     = rng.choice(CLAIM_TYPES[ptype])
    is_fraud  = rng.random() < FRAUD_RATE

    # Base claim amount by policy type, inflated for fraud
    base = {"Auto": 4000, "Home": 8000, "Health": 3000,
            "Travel": 1500, "Life": 50000, "Commercial": 25000}[ptype]
    amount = rng.gamma(2.0, base / 2.0)
    if is_fraud:
        amount *= rng.uniform(1.8, 3.5)          # fraud → larger payouts

    claim_date  = start_window + timedelta(days=int(rng.integers(0, 730)))
    # Fraud tends to be filed quickly after incident
    report_lag  = int(rng.integers(0, 3)) if is_fraud else int(rng.integers(0, 30))
    report_date = claim_date + timedelta(days=report_lag)

    # Fraud skews toward certain channels
    if is_fraud:
        channel = rng.choice(CHANNELS, p=[0.10, 0.40, 0.10, 0.10, 0.30])
    else:
        channel = rng.choice(CHANNELS)

    # Status distribution differs for fraud
    if is_fraud:
        status = rng.choice(CLAIM_STATUS, p=[0.25, 0.35, 0.15, 0.25])
    else:
        status = rng.choice(CLAIM_STATUS, p=[0.60, 0.10, 0.15, 0.15])

    rows.append({
        "claim_id":            f"CLM{500000 + i}",
        "policyholder_id":     ph["policyholder_id"],
        "policy_type":         ptype,
        "claim_type":          ctype,
        "region":              ph["region"],
        "channel":             channel,
        "claim_date":          claim_date.date(),
        "report_date":         report_date.date(),
        "report_lag_days":     report_lag,
        "claim_amount":        round(float(amount), 2),
        "num_prior_claims":    int(rng.integers(0, 8)),
        "witnesses":           int(rng.integers(0, 4)),
        "police_report_filed": bool(rng.random() < (0.3 if is_fraud else 0.7)),
        "claim_status":        status,
        "is_fraud":            int(is_fraud),
    })

claims = pd.DataFrame(rows)
print(f"claims: {claims.shape}  |  fraud rate: {claims['is_fraud'].mean():.2%}")
claims.head()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 7 · Inject a few realistic data-quality issues
# MAGIC So the Bronze→Silver cleaning step in Visual Data Prep has real work to do
# MAGIC (nulls, negative amounts, duplicate rows, whitespace).

# COMMAND ----------

# 1% null claim_amount
null_idx = rng.choice(claims.index, size=int(0.01 * len(claims)), replace=False)
claims.loc[null_idx, "claim_amount"] = np.nan

# A handful of negative amounts (data entry errors)
neg_idx = rng.choice(claims.index, size=15, replace=False)
claims.loc[neg_idx, "claim_amount"] = claims.loc[neg_idx, "claim_amount"].fillna(1000) * -1

# Some whitespace / case noise in region
noise_idx = rng.choice(claims.index, size=30, replace=False)
claims.loc[noise_idx, "region"] = "  " + claims.loc[noise_idx, "region"].str.upper() + " "

# A few exact duplicate claims
dupes = claims.sample(20, random_state=SEED)
claims = pd.concat([claims, dupes], ignore_index=True)

print(f"claims after DQ injection: {claims.shape}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 8 · Write CSV and Parquet to the volume
# MAGIC `claims` is written as CSV, `policyholders` as Parquet — so the Bronze loader demonstrates both formats.

# COMMAND ----------

claims_csv        = f"{INPUT_PATH}/claims.csv"
claims_parquet    = f"{INPUT_PATH}/claims.parquet"
holders_parquet   = f"{INPUT_PATH}/policyholders.parquet"
holders_csv       = f"{INPUT_PATH}/policyholders.csv"

# pandas can write straight to the /Volumes fuse mount
claims.to_csv(claims_csv, index=False)
claims.to_parquet(claims_parquet, index=False)
policyholders.to_parquet(holders_parquet, index=False)
policyholders.to_csv(holders_csv, index=False)

print("✅ Files written:")
for f in dbutils.fs.ls(INPUT_PATH):
    print(f"  {f.name:28s} {f.size/1024:,.1f} KB")

# COMMAND ----------

# MAGIC %md
# MAGIC ### ✅ Data generation complete
# MAGIC You now have **5,000+ claims** and **1,500 policyholders** in `raw/input`.
# MAGIC Next: run **`03_load_to_bronze`** to ingest these files into Bronze Delta tables.

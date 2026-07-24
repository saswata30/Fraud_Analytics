# Databricks notebook source
# MAGIC %md
# MAGIC # _config — shared catalog/schema resolution
# MAGIC
# MAGIC Every executable notebook runs this first via `%run ./_config`. It resolves a catalog that
# MAGIC works in **whatever workspace you're in** (a Vocareum lab, FEVM, or a demo workspace), so the
# MAGIC notebooks don't depend on a hard-coded catalog that may not exist.
# MAGIC
# MAGIC Resolution order:
# MAGIC 1. Try to **create** a Unity Catalog named `allianz_workshop` (then `fraud_analytics`) — used if you have `CREATE CATALOG`.
# MAGIC 2. Else reuse an **existing writable** catalog (`main`, or the workspace's managed catalog).
# MAGIC 3. Else fall back to **`hive_metastore`** (legacy; almost always writable in a lab).
# MAGIC
# MAGIC After running, these variables are available to the caller: `CATALOG`, `SCHEMA`, `FQ`,
# MAGIC `VOLUME`, `INPUT_PATH`, `USERDATA_PATH`.

# COMMAND ----------

SCHEMA = "fraud_analytics"
VOLUME = "raw"

# Preferred catalogs to CREATE (first that succeeds wins)
_PREFERRED = ["allianz_workshop", "fraud_analytics"]
# Existing catalogs to fall back to (must allow CREATE SCHEMA)
_FALLBACK = ["main", "hive_metastore"]


def _can_use(cat: str) -> bool:
    """True if we can create a schema in this catalog (probe then clean up)."""
    try:
        spark.sql(f"CREATE SCHEMA IF NOT EXISTS `{cat}`.`_fa_probe`")
        spark.sql(f"DROP SCHEMA IF EXISTS `{cat}`.`_fa_probe`")
        return True
    except Exception:
        return False


def _resolve_catalog() -> str:
    # 1. try to create a preferred UC catalog
    for c in _PREFERRED:
        try:
            spark.sql(f"CREATE CATALOG IF NOT EXISTS `{c}`")
            if _can_use(c):
                print(f"✅ Using catalog (created/owned): {c}")
                return c
        except Exception as e:
            print(f"  · cannot create catalog '{c}': {str(e)[:120]}")
    # 2. reuse an existing writable catalog
    for c in _FALLBACK:
        if _can_use(c):
            print(f"➡️  Falling back to existing catalog: {c}")
            return c
    # 3. last resort — try any catalog the user can see that is writable
    try:
        for row in spark.sql("SHOW CATALOGS").collect():
            c = row[0]
            if c not in ("samples",) and _can_use(c):
                print(f"➡️  Falling back to discovered catalog: {c}")
                return c
    except Exception:
        pass
    print("⚠️  No writable catalog found; defaulting to hive_metastore.")
    return "hive_metastore"


CATALOG = _resolve_catalog()
FQ = f"{CATALOG}.{SCHEMA}"

spark.sql(f"CREATE SCHEMA IF NOT EXISTS {FQ}")
spark.sql(f"USE CATALOG {CATALOG}")
spark.sql(f"USE SCHEMA {SCHEMA}")

INPUT_PATH = f"/Volumes/{CATALOG}/{SCHEMA}/{VOLUME}/input"
USERDATA_PATH = f"{INPUT_PATH}/userdata"

print(f"CATALOG={CATALOG}  SCHEMA={SCHEMA}  FQ={FQ}")

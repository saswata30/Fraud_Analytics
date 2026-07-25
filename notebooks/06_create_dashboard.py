# Databricks notebook source
# MAGIC %md
# MAGIC # 06 · Create the Fraud Analytics Dashboard — *Business-User Prompts*
# MAGIC
# MAGIC Build a polished, **enterprise-ready** AI/BI (Lakeview) dashboard **without writing any SQL**.
# MAGIC Everything below is a plain-English prompt you paste into the dashboard **Assistant** (the ✨
# MAGIC icon). The Assistant reads the Gold tables and builds each tile for you.
# MAGIC
# MAGIC The dashboard tells one story in three sections:
# MAGIC
# MAGIC | Section | Question it answers | Tiles |
# MAGIC |---------|--------------------|-------|
# MAGIC | 🎯 **Fraud Detection** | *How much fraud is there, and where?* | headline KPIs, fraud by region, fraud by policy, risk mix |
# MAGIC | 📈 **Trend** | *Is fraud getting better or worse over time?* | fraud-rate trend, claim-volume trend, payout trend |
# MAGIC | 💷 **Impact** | *What is it costing us, and which claims to act on?* | flagged payout, exposure, top high-risk claims |
# MAGIC
# MAGIC A **date-range filter** (plus region and policy) sits at the top and controls every tile.
# MAGIC
# MAGIC > **No code to run here.** Attach nothing — just open the Assistant and paste the prompts in order.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Before you start (30 seconds)
# MAGIC 1. Left sidebar → **Dashboards → Create dashboard**. Name it **`Fraud Analytics — Executive Overview`**.
# MAGIC 2. On the **Data** tab, click **Add from Unity Catalog** and add these two Gold tables (no SQL needed):
# MAGIC    - **`gold_fraud_claims`** — one row per claim (the fraud label + risk score live here)
# MAGIC    - **`gold_fraud_by_region`** — fraud totals by region and policy type
# MAGIC
# MAGIC    They're in the **`fraud_analytics`** schema. If you can't find them, ask your workshop lead which
# MAGIC    **catalog** to pick — the tables are always `…​.fraud_analytics.gold_fraud_claims` and
# MAGIC    `…​.fraud_analytics.gold_fraud_by_region`.
# MAGIC 3. Open the **Assistant** (✨, top-right of the canvas) and paste the prompts below **one at a time**.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Prompt 0 · Set the look & feel (paste this first)
# MAGIC ```
# MAGIC Style this as a clean, professional executive dashboard for insurance fraud.
# MAGIC - Use a light theme with plenty of white space and a clear visual hierarchy: a bold title row,
# MAGIC   then KPI tiles, then charts grouped into sections.
# MAGIC - Consistent colour language across every tile: use RED for fraud / high risk, GREY or BLUE for
# MAGIC   legitimate / neutral, and AMBER for warnings or money-at-risk.
# MAGIC - Format all money as GBP (£) with thousands separators, and all rates as percentages with one decimal.
# MAGIC - Give every tile a short, plain-English title a business user understands (e.g. "Fraud Rate",
# MAGIC   "Money Flagged as Fraud"), not a table or column name.
# MAGIC - Add three markdown section headers as I build: "Fraud Detection", "Trend Over Time", and
# MAGIC   "Financial Impact".
# MAGIC ```

# COMMAND ----------

# MAGIC %md
# MAGIC ## Prompt 1 · Global filters — including the date range
# MAGIC ```
# MAGIC Add a filter bar pinned to the top of the dashboard that controls ALL tiles:
# MAGIC - A DATE RANGE filter on the claim date (claim_date in gold_fraud_claims). Default it to the
# MAGIC   last 12 months, and let me pick presets like Last 30 days, Last quarter, Year to date, and All time.
# MAGIC - A dropdown filter on Region.
# MAGIC - A dropdown filter on Policy Type.
# MAGIC Make all three cross-filter every KPI and chart on the page.
# MAGIC ```

# COMMAND ----------

# MAGIC %md
# MAGIC ## 🎯 Section 1 · Fraud Detection
# MAGIC *How much fraud is there, and where is it concentrated?*

# COMMAND ----------

# MAGIC %md
# MAGIC ### Prompt 2 · Headline KPI tiles
# MAGIC ```
# MAGIC Under a "Fraud Detection" header, create a row of 5 big KPI counter tiles from gold_fraud_claims,
# MAGIC each respecting the date-range and other filters:
# MAGIC 1. "Fraud Rate" — the share of claims flagged as fraud (average of the fraud flag), as a percentage. Colour it red.
# MAGIC 2. "Confirmed Fraud Claims" — the count of fraudulent claims.
# MAGIC 3. "Total Claims" — the count of all claims.
# MAGIC 4. "High-Risk Claims" — the count of claims with a fraud risk score of 3 or higher (amber).
# MAGIC 5. "Avg Claim Value" — the average claim amount in GBP.
# MAGIC Show a small up/down comparison vs the previous period where possible.
# MAGIC ```

# COMMAND ----------

# MAGIC %md
# MAGIC ### Prompt 3 · Where fraud is concentrated
# MAGIC ```
# MAGIC Add two horizontal bar charts side by side, sorted from highest to lowest fraud rate:
# MAGIC - "Fraud Rate by Region" — fraud rate per region.
# MAGIC - "Fraud Rate by Policy Type" — fraud rate per policy type.
# MAGIC Colour the bars on a red scale so the worst areas stand out, and label each bar with its percentage.
# MAGIC ```

# COMMAND ----------

# MAGIC %md
# MAGIC ### Prompt 4 · Risk mix
# MAGIC ```
# MAGIC Add two tiles:
# MAGIC - A donut "Fraud vs Legitimate Claims" showing the split of claims by the fraud flag,
# MAGIC   with fraud in red and legitimate in grey, and the fraud percentage shown in the centre.
# MAGIC - A column chart "Risk-Score Distribution" showing how many claims fall into each fraud risk
# MAGIC   score from 0 to 4, split into fraud (red) and legitimate (grey) within each bar.
# MAGIC ```

# COMMAND ----------

# MAGIC %md
# MAGIC ## 📈 Section 2 · Trend Over Time
# MAGIC *Is fraud getting better or worse — and is the business growing?*

# COMMAND ----------

# MAGIC %md
# MAGIC ### Prompt 5 · Fraud trend
# MAGIC ```
# MAGIC Under a "Trend Over Time" header, add a line chart "Fraud Rate Over Time" using the claim month
# MAGIC (claim_month) on the x-axis and the fraud rate on the y-axis, as a red line with markers.
# MAGIC Add a subtle target or average reference line so viewers can see when we're above normal.
# MAGIC The date-range filter should zoom this chart.
# MAGIC ```

# COMMAND ----------

# MAGIC %md
# MAGIC ### Prompt 6 · Volume & money trend together
# MAGIC ```
# MAGIC Add a combo chart "Claims & Flagged Payout Over Time" by claim month:
# MAGIC - Columns = total number of claims per month (grey).
# MAGIC - Line = total money flagged as fraud per month (sum of claim amount where the claim is fraud), in GBP, on a secondary axis (red).
# MAGIC This shows whether rising fraud cost is driven by more claims or bigger fraudulent ones.
# MAGIC ```

# COMMAND ----------

# MAGIC %md
# MAGIC ## 💷 Section 3 · Financial Impact
# MAGIC *What is fraud costing us, and which claims should we act on now?*

# COMMAND ----------

# MAGIC %md
# MAGIC ### Prompt 7 · Impact KPIs
# MAGIC ```
# MAGIC Under a "Financial Impact" header, add a row of 3 KPI tiles from gold_fraud_claims (respecting all filters):
# MAGIC 1. "Money Flagged as Fraud" — total claim amount for fraudulent claims, in GBP (red).
# MAGIC 2. "Total Claims Payout" — total claim amount across all claims, in GBP.
# MAGIC 3. "Fraud Loss Ratio" — money flagged as fraud divided by total payout, as a percentage (amber).
# MAGIC ```

# COMMAND ----------

# MAGIC %md
# MAGIC ### Prompt 8 · Where the money is at risk
# MAGIC ```
# MAGIC Add a horizontal bar chart "Flagged Payout by Region" showing the total money flagged as fraud
# MAGIC per region, in GBP, sorted largest first, coloured amber. This tells us where to focus recovery effort.
# MAGIC ```

# COMMAND ----------

# MAGIC %md
# MAGIC ### Prompt 9 · The action list
# MAGIC ```
# MAGIC Add a table "Highest-Risk Claims to Review" from gold_fraud_claims, sorted by fraud risk score
# MAGIC (highest first) then by claim amount, showing the top 25 rows with these business-friendly columns:
# MAGIC Claim ID, Region, Policy Type, Channel, Claim Amount (GBP), Risk Score, and a Fraud? Yes/No column.
# MAGIC Colour the Risk Score as a pill: grey for 0-1, amber for 2, red for 3-4. This is the queue an
# MAGIC investigator works through.
# MAGIC ```

# COMMAND ----------

# MAGIC %md
# MAGIC ## Prompt 10 · Final polish
# MAGIC ```
# MAGIC Tidy the layout for an executive audience:
# MAGIC - Arrange tiles in neat rows with equal spacing; KPIs on top of each section, charts below.
# MAGIC - Make sure every tile title is plain English and every number is formatted (£ for money, % for rates).
# MAGIC - Add a one-line dashboard description under the title: "Insurance fraud detection, trends and
# MAGIC   financial impact — filter by date, region and policy type."
# MAGIC - Double-check the date-range filter controls every tile.
# MAGIC ```

# COMMAND ----------

# MAGIC %md
# MAGIC ## Publish & share
# MAGIC - Click **Publish**. Choose **"run as owner"** (or a service principal with read access) so viewers
# MAGIC   don't each need table permissions.
# MAGIC - **Share** with your business stakeholders, and optionally set a **refresh schedule**.
# MAGIC - Add an **"Open in Genie"** link so a viewer can drill from any chart into a natural-language
# MAGIC   follow-up question (Genie Space from notebook `05`).

# COMMAND ----------

# MAGIC %md
# MAGIC ### ✅ Dashboard complete
# MAGIC You now have an enterprise-ready fraud dashboard — **Detection · Trend · Impact**, with a global
# MAGIC date range — built entirely from business prompts. It's one of three surfaces over the same Gold
# MAGIC tables: **Dashboard** (this notebook) · **Genie Space** (`05`) · **App** (`07`, optional).

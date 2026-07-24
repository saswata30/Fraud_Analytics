# Special Investigations Unit — Suspected Organised Motor & Home Claims Fraud Ring

**Allianz Workshop — Fraud Analytics Reference Document**
**Classification:** Internal — Special Investigations Unit (SIU)
**Report reference:** SIU-2024-0417
**Prepared by:** Claims Intelligence & Fraud Analytics
**Reporting period:** January 2023 – December 2024
**Status:** Referred to Financial Conduct pathway; three claims denied, two under review

> This is a synthetic reference document created for the Fraud Analytics workshop. All
> policyholders, claim identifiers, and events are fictional. It is designed to be uploaded
> into the "Ask Genie" assistant so users can ask questions grounded in both this narrative
> and the underlying `gold_fraud_claims` dataset. Where possible it uses the same fields the
> data uses — `policy_type`, `claim_type`, `region`, `channel`, `report_lag_days`,
> `claim_amount`, `fraud_risk_score`, `num_prior_claims`, and the `is_fraud` label.

---

## 1. Executive Summary

Between January 2023 and December 2024, the Special Investigations Unit (SIU) identified a
cluster of claims exhibiting a consistent and statistically improbable pattern. The cluster
spans **Auto** and **Home** policy lines, is concentrated in the **London** and **North West**
regions, and is overwhelmingly submitted through the **Online** and **Mobile App** channels.
The claims share four recurring characteristics that, individually, are unremarkable but, in
combination, drive the internal `fraud_risk_score` to 3 or 4 on the 0–4 scale:

1. **High claim value** — payouts materially above the portfolio average for the relevant
   policy type (the `high_value_flag`, triggered above £20,000).
2. **Fast reporting** — incidents reported within 0–2 days of the stated claim date
   (the `fast_report_flag`, `report_lag_days <= 2`).
3. **New customer tenure** — policies opened less than twelve months before the loss event
   (the `new_customer_flag`, `tenure_years < 1`).
4. **Low credit score** — policyholder credit scores below 500 at inception
   (the `low_credit_flag`).

Of the 41 claims in the cluster, **29 carried a `fraud_risk_score` of 3 or higher** and 17 were
ultimately confirmed as fraudulent (`is_fraud = 1`). The estimated exposure avoided through early
detection and denial is approximately **£612,000** in gross claim payout.

The purpose of this document is threefold: (a) to record the investigative narrative for audit;
(b) to describe the behavioural and data signals that distinguished this ring from the
legitimate claims population; and (c) to provide a reference an analyst can interrogate using
natural-language questions against the governed claims data.

---

## 2. Background and Trigger

The investigation was triggered by an automated alert from the fraud analytics pipeline. During
the routine Bronze → Silver → Gold refresh, the aggregate table `gold_fraud_by_region` surfaced
an anomaly: the **fraud rate for Auto claims in London rose from a baseline of roughly 7% to over
19%** across two consecutive months, while claim volume in the same segment rose only modestly.
A rise in fraud *rate* that is not explained by a proportional rise in overall claim *volume* is
a classic indicator of a coordinated push rather than organic growth.

A secondary trigger came from the **channel mix**. In the legitimate population, claims are
distributed fairly evenly across Branch, Online, Broker, Call Center, and Mobile App. Within the
flagged cluster, **over 70% of claims originated from Online and Mobile App channels** — the two
channels with the lowest friction and least human interaction at first notice of loss (FNOL).
This is consistent with the hypothesis that the ring deliberately favoured self-service channels
to minimise the chance of an adjuster detecting inconsistencies during a phone or in-person FNOL.

The SIU opened case SIU-2024-0417 and pulled the underlying claim-level records for manual review.

---

## 3. Anatomy of the Cluster

### 3.1 Policy and claim composition

The 41 claims broke down as follows:

- **Auto (26 claims):** predominantly `Collision` and `Theft` claim types. Several "theft"
  claims involved vehicles reported stolen within days of a newly added comprehensive cover.
- **Home (12 claims):** predominantly `Burglary` and `Accidental Damage`. A recurring feature
  was high-value contents claims (jewellery, electronics) with limited proof of ownership.
- **Travel (3 claims):** `Lost Luggage` and `Cancellation`, appended to the ring later and of
  lower value; included here because they shared policyholder linkages.

### 3.2 The four-signal fingerprint

The single most useful analytic artefact was the `fraud_risk_score`, which is the sum of the four
boolean flags described in the Executive Summary. The distribution within the cluster was starkly
different from the book as a whole:

| Risk score | Cluster claims | Portfolio baseline (approx.) |
|-----------:|---------------:|-----------------------------:|
| 0          | 1              | 34%                          |
| 1          | 4              | 33%                          |
| 2          | 7              | 20%                          |
| 3          | 18             | 9%                           |
| 4          | 11             | 4%                           |

In plain terms: in the normal book, roughly one claim in eight scores 3 or 4. In this cluster,
**more than seven in ten did.** A score of 4 — where all four indicators fire at once — is rare
enough in the legitimate population that it warrants manual review on its own.

### 3.3 Reporting-lag behaviour

Legitimate claimants report losses with a wide spread of delays; genuine policyholders often take
one to four weeks to gather documents, obtain repair estimates, or simply get around to filing.
The `report_lag_days` field in the cluster told a different story: **the median reporting lag was
1 day**, and 33 of 41 claims were reported within 48 hours of the stated incident date. Fast
reporting is not proof of fraud — a stolen car is often reported immediately — but a *cluster* of
uniformly fast reporting, combined with the other signals, is a meaningful escalation factor.

### 3.4 Prior-claims and tenure linkage

Cross-referencing the `policyholders` dimension revealed that a disproportionate number of the
policyholders in the cluster had:

- **Short tenure:** `customer_since` dates within twelve months of the loss (the
  `new_customer_flag`). Fraud rings frequently open fresh policies specifically to stage a loss.
- **Elevated prior-claim counts:** several policyholders showed `num_prior_claims` of 4 or more
  despite short tenure — an implausible combination for genuine customers.
- **Low credit scores:** median credit score in the cluster was 430, versus a portfolio median
  near 575.

---

## 4. Illustrative Cases

The following cases are representative. Identifiers follow the workshop dataset convention
(`CLM…` for claims, `PH…` for policyholders) and are fictional.

### Case A — Auto / Theft (score 4, confirmed fraud)

A comprehensive Auto policy was opened Online in the North West. Eleven days later, the insured
vehicle — a high-value SUV — was reported stolen, with the claim filed the same day (`report_lag_days = 0`).
The claim amount was approximately £34,000, well above the Auto average, triggering
`high_value_flag`. The policyholder's credit score was 402 (`low_credit_flag`), tenure was under
one month (`new_customer_flag`), and reporting was immediate (`fast_report_flag`). All four flags
fired: `fraud_risk_score = 4`. Investigation found the vehicle had been exported before the policy
was opened. **Outcome: claim denied, `is_fraud = 1`.**

### Case B — Home / Burglary (score 3, confirmed fraud)

A Home contents claim in London reported a burglary of jewellery and electronics totalling
£28,500. Reported within one day. The policyholder had four prior claims across two lines despite
holding the policy for only eight months. No police report was filed (`police_report_filed = false`),
which is atypical for a genuine burglary of that value. Three flags fired. **Outcome: claim denied,
`is_fraud = 1`.**

### Case C — Auto / Collision (score 2, legitimate)

Included as a **counter-example**. A collision claim in London for £22,000 triggered
`high_value_flag` and, because the driver was a recent switch, `new_customer_flag`. However, the
claim was reported after nine days (no `fast_report_flag`), the credit score was 690 (no
`low_credit_flag`), a police report was filed, and there were no prior claims. Score of 2. Manual
review cleared it. **Outcome: claim paid, `is_fraud = 0`.** This case underscores that a high
value alone is not fraud; it is the *combination* of signals that matters.

---

## 5. Analytical Method

The SIU's approach combined rule-based flags with human judgement:

1. **Segment isolation.** Filter `gold_fraud_claims` to the affected segments (Auto/Home,
   London/North West, Online/Mobile App).
2. **Score triage.** Rank by `fraud_risk_score` descending, then by `claim_amount` descending.
   Claims scoring 3–4 were queued for manual review first.
3. **Entity resolution.** Join to the `policyholders` dimension on `policyholder_id` to expose
   tenure, prior-claim counts, and credit score, and to detect shared attributes across
   claimants (addresses, contact details, repeat payees).
4. **Behavioural overlay.** Examine `report_lag_days`, `police_report_filed`, and `witnesses`
   for patterns inconsistent with genuine losses.
5. **Disposition.** Deny, refer, or clear. Every disposition was logged for audit and to create
   labelled training data (`is_fraud`) for future model development.

The key lesson for analysts: **no single field convicts a claim.** The `high_value_flag` catches
expensive genuine claims; `fast_report_flag` catches conscientious genuine claimants. It is the
*co-occurrence* of indicators — captured compactly by `fraud_risk_score` — plus corroborating
entity linkage, that separates organised fraud from noise.

---

## 6. Financial Impact

- **Claims in cluster:** 41
- **Confirmed fraudulent (`is_fraud = 1`):** 17
- **Gross payout avoided (denied claims):** ≈ £612,000
- **Under review at time of writing:** 2 (≈ £47,000 combined exposure)
- **False-positive rate on manual review:** ~19% (claims flagged but cleared) — considered
  acceptable given the exposure avoided, but a target for model refinement.

---

## 7. Recommendations

1. **Elevate `fraud_risk_score = 4` claims to mandatory manual review** before any payment,
   regardless of policy line.
2. **Add friction at FNOL for Online/Mobile App high-value claims** from new customers —
   e.g. mandatory document upload or a call-back step.
3. **Monitor `gold_fraud_by_region` for rate-without-volume anomalies** as a standing alert.
4. **Feed dispositions back as labels** to move from rules toward a supervised fraud model.
5. **Review the false-positive population** to tune thresholds and reduce genuine-customer
   friction.

---

## 8. Appendix — Field Glossary (as used in the data)

| Field | Meaning |
|-------|---------|
| `claim_amount` | Claim payout value in GBP |
| `report_lag_days` | Days between incident date and report date |
| `num_prior_claims` | Count of prior claims by the policyholder |
| `police_report_filed` | Whether a police report was filed |
| `fraud_risk_score` | 0–4 sum of high-value, fast-report, new-customer, low-credit flags |
| `is_fraud` | Ground-truth label: 1 = confirmed fraud, 0 = legitimate |

*End of report SIU-2024-0417.*

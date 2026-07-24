# EU Regulatory & Compliance Framework for Insurance Fraud Analytics

**Allianz Workshop — Fraud Analytics Reference Document**
**Document type:** Compliance policy & control framework
**Reference:** COMP-EU-FRAUD-2024
**Owner:** Group Compliance & Data Protection Office
**Applies to:** Automated and analyst-assisted insurance fraud detection across the EU/EEA
**Version:** 1.0

> This is a synthetic reference document for the Fraud Analytics workshop. It summarises the
> principal EU obligations that govern how an insurer may use data and automated analytics to
> detect fraud. It is written to be uploaded into the "Ask Genie" assistant so users can ask
> compliance questions and cross-reference them against the fraud dataset (for example, "which
> fields in the data are personal data under GDPR?"). It is **not legal advice** and is
> deliberately generalised for teaching purposes.

---

## 1. Purpose and Scope

This framework sets out the regulatory obligations and internal controls that apply when the
firm uses personal data and automated analytics to detect, investigate, and act upon suspected
insurance fraud within the European Union and the wider European Economic Area (EEA).

It covers the full fraud analytics lifecycle as implemented in this workshop:

- ingestion of raw claims and policyholder data into the **Bronze** layer;
- cleaning and enrichment into **Silver** and **Gold** (including derived fields such as
  `fraud_risk_score` and the four risk flags);
- natural-language querying of governed data via Genie;
- analyst decisions to pay, deny, or refer a claim.

The dataset in scope contains both non-personal claim attributes (e.g. `policy_type`,
`claim_amount`, `region`) and **personal data** relating to identifiable individuals
(e.g. `policyholder_id`, `full_name`, `date_of_birth`, `email`, `phone`, `credit_score`). The
presence of personal data brings the activity squarely within the GDPR.

---

## 2. Legal Bases and Governing Instruments

The following EU instruments are most relevant to fraud analytics:

### 2.1 General Data Protection Regulation (GDPR) — Regulation (EU) 2016/679

The GDPR is the central instrument. Fraud detection is expressly recognised as a **legitimate
interest** of a data controller (Recital 47 notes that processing personal data strictly
necessary for fraud prevention constitutes a legitimate interest). The firm therefore typically
relies on:

- **Article 6(1)(f) — legitimate interests** as the lawful basis for fraud-detection processing,
  supported by a documented Legitimate Interests Assessment (LIA) balancing the firm's interest
  against the rights of data subjects; and
- **Article 6(1)(c) — legal obligation**, where anti-fraud or anti-money-laundering law compels
  processing.

Where the analytics touch **special category data** (Article 9) — for example health data in a
Health claim — an additional Article 9 condition is required, such as reasons of substantial
public interest laid down in Member State law.

### 2.2 Article 22 — Automated Decision-Making

Article 22 grants data subjects the right **not to be subject to a decision based solely on
automated processing** (including profiling) that produces legal or similarly significant
effects. Denying an insurance claim is a "similarly significant effect."

**Control implication for this workshop:** the `fraud_risk_score` and the four flags are used to
**triage and rank** claims for human review — they must **not** auto-deny a claim. A qualified
analyst (the human-in-the-loop) makes the final disposition. This preserves the exception in
Article 22(2) and the safeguards in Article 22(3): the right to obtain human intervention, to
express a point of view, and to contest the decision.

### 2.3 Data Governance and the AI Act

- **Regulation (EU) 2022/868 (Data Governance Act)** and **Regulation (EU) 2023/2854 (Data Act)**
  shape how data may be shared and reused.
- **The EU AI Act (Regulation (EU) 2024/1689)** classifies certain AI systems by risk. Systems
  used for **risk assessment and pricing in life and health insurance** are treated as
  **high-risk** and attract obligations on data quality, logging, transparency, human oversight,
  and accuracy. A fraud-triage model that materially affects access to an insurance benefit
  should be assessed against these obligations; even where a system is not formally high-risk,
  the AI Act's principles (human oversight, transparency, robustness) are sound practice.

### 2.4 Insurance-specific and financial-crime rules

- **Insurance Distribution Directive (Directive (EU) 2016/97)** — conduct and customer-treatment
  obligations that constrain how fraud suspicion is acted upon.
- **Anti-Money-Laundering framework (Directive (EU) 2015/849 as amended)** — where fraud
  intersects with money laundering, suspicious activity reporting obligations apply.

---

## 3. Core Data-Protection Principles Applied to Fraud Analytics

The GDPR's Article 5 principles map onto the pipeline as follows.

### 3.1 Lawfulness, fairness, transparency
Policyholders must be told, in the privacy notice, that their data may be processed for fraud
prevention. Fairness requires that the analytics do not produce discriminatory outcomes against
protected groups.

### 3.2 Purpose limitation
Data collected for underwriting and claims handling may be reused for fraud detection because
that purpose is compatible and disclosed. It may **not** be silently repurposed for unrelated
marketing.

### 3.3 Data minimisation
Only data necessary for fraud detection should be processed. **Control implication:** the Silver
layer in this workshop deliberately **drops direct-contact PII (`email`, `phone`)** when building
`silver_policyholders`, retaining only what the analytics need (region, tenure, credit score,
age). Analysts querying via Genie should not need raw contact details to assess fraud risk.

### 3.4 Accuracy
Fraud flags and scores must be based on accurate data. The pipeline's **data-quality
expectations** (unique non-null `claim_id`, `claim_amount > 0`, `report_date >= claim_date`,
`is_fraud ∈ {0,1}`) directly support this principle. Inaccurate data that wrongly flags a
genuine customer is both a compliance and a fairness failure.

### 3.5 Storage limitation
Personal data must not be kept longer than necessary. Fraud-investigation records may be retained
for a defined period to defend decisions and meet legal obligations, then deleted or anonymised.

### 3.6 Integrity and confidentiality
Access to governed data must be controlled. **Control implication:** Unity Catalog enforces
table- and column-level access; the Databricks App runs under a service principal with least-
privilege `SELECT` grants; and all access is auditable.

### 3.7 Accountability
The firm must be able to **demonstrate** compliance — through this framework, the LIA, a Data
Protection Impact Assessment (DPIA), lineage in Unity Catalog, and an audit trail of analyst
decisions.

---

## 4. Data Subject Rights

Fraud detection interacts with data subject rights in specific ways:

- **Right to information (Arts 13–14):** the privacy notice must disclose fraud processing and,
  where automated decision-making with significant effect occurs, provide meaningful information
  about the logic involved.
- **Right of access (Art 15):** subjects may request their data. Access can be **restricted where
  disclosure would tip off a fraudster** or prejudice an ongoing investigation, but the
  restriction must be necessary and proportionate and recorded.
- **Right to rectification (Art 16):** genuine data errors must be corrected — important where an
  inaccurate credit score or tenure wrongly inflated a risk score.
- **Right to object (Art 21):** subjects may object to legitimate-interests processing; the firm
  must weigh this against compelling grounds for fraud prevention.
- **Rights re automated decisions (Art 22):** human intervention, the ability to express a view,
  and to contest the outcome — satisfied by the human-in-the-loop analyst model.

---

## 5. Required Controls and Governance

The following controls are mandatory for any fraud analytics system in scope.

### 5.1 Documentation
- A current **DPIA** for the fraud analytics activity (Article 35 — likely required given
  large-scale profiling of individuals).
- A documented **Legitimate Interests Assessment**.
- A **Record of Processing Activities** (Article 30).

### 5.2 Human oversight
- Automated scores **triage** but never **auto-deny**. A qualified analyst reviews and dispositions
  every high-risk claim.
- Analysts are trained on both fraud indicators and non-discrimination obligations.

### 5.3 Fairness and non-discrimination
- Periodic testing of outcomes across protected characteristics to detect disparate impact.
- Special-category proxies (e.g. using `region` or `gender` in a way that proxies for ethnicity)
  must be reviewed and justified or removed.

### 5.4 Security and access
- Least-privilege access via Unity Catalog; column masking of PII where feasible.
- Full audit logging of who accessed which governed data and what dispositions were made.

### 5.5 Explainability
- The basis of a fraud flag must be explainable to the data subject and to a regulator. The
  transparent, additive `fraud_risk_score` (four named flags) is preferred over an opaque model
  for exactly this reason in a teaching context.

---

## 6. Mapping Data Fields to Compliance Categories

| Data field | Category | Notes |
|------------|----------|-------|
| `policyholder_id` | Pseudonymous identifier | Personal data when linkable to a person |
| `full_name`, `email`, `phone` | Direct PII | Minimised — dropped from Silver policyholders |
| `date_of_birth` / derived `customer_age` | Personal data | Age can proxy for protected traits — monitor |
| `credit_score` | Personal data (financial) | Sensitive; central to `low_credit_flag` |
| `region` | Personal data (location) | Watch for geographic proxy discrimination |
| `gender` | Special-category-adjacent | Must not drive fraud decisions |
| `claim_amount`, `claim_type`, `policy_type` | Non-personal claim attributes | Low risk |
| `fraud_risk_score`, `is_fraud` | Derived assessment / label | Governed by Article 22 safeguards |

---

## 7. Breach and Incident Response

Any personal-data breach affecting fraud analytics data (e.g. unauthorised access to the Gold
tables) must be assessed within the GDPR's **72-hour** notification window (Article 33) and, where
high risk to individuals arises, the affected individuals notified (Article 34). The audit trail
in Unity Catalog supports rapid scoping of any breach.

---

## 8. Summary of Obligations Checklist

- [ ] Lawful basis documented (legitimate interests / legal obligation).
- [ ] DPIA completed and current.
- [ ] Article 22 respected — human-in-the-loop, no solely-automated denial.
- [ ] Data minimisation enforced (PII dropped where not needed).
- [ ] Data-quality expectations active on Silver/Gold.
- [ ] Access controlled and audited via Unity Catalog.
- [ ] Fairness testing across protected groups performed.
- [ ] Data subject rights process in place, including tipping-off safeguards.
- [ ] Retention schedule defined and enforced.

*End of framework COMP-EU-FRAUD-2024. Not legal advice — synthetic teaching material.*

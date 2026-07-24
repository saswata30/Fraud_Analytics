# Genie Sample Questions — Fraud Analytics

A ready-to-use set of natural-language questions for the **Insurance Fraud Analytics** Genie
Space (and the "Ask Genie" panel in the app). They are grouped from simple to advanced. Most run
directly against `gold_fraud_claims` / `gold_fraud_by_region`. The last group is for use **after
uploading one of the sample documents** in `docs/` (the SIU fraud report or the EU compliance
policy), where the answer blends the document with the data.

> Tip: the expected-SQL column is a guide for benchmarking (notebook `05`), not something the
> user types. Genie generates its own SQL from the natural-language question.

---

## A. Warm-up (single metric)

1. **What is the overall fraud rate?**
   _Expected: `SELECT SUM(is_fraud)/COUNT(*) FROM gold_fraud_claims;` ≈ 0.07_

2. **How many claims are in the dataset in total?**

3. **What is the total payout across all claims, and how much of it is on fraudulent claims?**

## B. Breakdowns (group-by)

4. **Which regions have the highest fraud rate?**
   _Expected: group by `region`, order by fraud rate desc._

5. **Show the fraud rate by policy type, from highest to lowest.**

6. **Which channel has the most fraudulent claims — Branch, Online, Broker, Call Center, or Mobile App?**

7. **What is the average claim amount for fraudulent claims versus legitimate claims?**

## C. Risk indicators

8. **How many high-risk claims are there, where the fraud risk score is 3 or higher?**

9. **What is the average fraud risk score for fraudulent claims compared with legitimate ones?**

10. **List the 10 highest-value fraudulent claims with their region and policy type.**

11. **How many claims were reported within 2 days of the incident and were also fraudulent?**

## D. Trends

12. **Show the monthly fraud rate over time.**

13. **Which month had the highest fraudulent payout?**

## E. Combined / analytical

14. **For Auto claims in London submitted online, what is the fraud rate and how many claims are there?**

15. **Which policy type and region combination has the worst fraud rate?**
    _Expected: from `gold_fraud_by_region`, order by `fraud_rate` desc, limit 1._

16. **Among new customers with low credit scores, how many claims were fraudulent?**

---

## F. Questions to ask *after uploading a document*

Upload a file from `docs/` in the "Ask Genie" panel (it is stored in
`raw/input/userdata`), then ask questions that combine the document with the data.

**After uploading `sample_fraud_event_report.md` (the SIU report):**

17. **Based on the uploaded investigation report, which regions and channels should I focus on,
    and what does the data show the fraud rate is for those segments?**

18. **The report describes a four-signal fingerprint. Show me claims in the data that match all
    four signals (fraud risk score of 4) and tell me how many were confirmed fraud.**

19. **The report mentions Case A was an Auto theft with immediate reporting. How many Auto theft
    claims in the data were reported within 1 day?**

**After uploading `sample_eu_compliance_policy.md` (the EU compliance framework):**

20. **According to the uploaded compliance framework, which fields in this dataset are considered
    personal data under GDPR?**

21. **The compliance document says automated scores must not auto-deny claims. Explain how the
    fraud risk score is used for triage rather than automated denial.**

22. **Which data fields does the compliance framework say should be dropped for data
    minimisation, and are they present in the gold table?**

---

## Notes for facilitators

- If Genie struggles with a question, add it as an **example query** in the Genie Space
  instructions (see notebook `05_genie_space_setup`) with the correct SQL — this teaches Genie
  the join and metric definitions.
- Questions 1–16 are also a good **benchmark set**; paste them into the Genie **Benchmarks** tab
  with expected SQL to measure accuracy.
- Document-grounded questions (17–22) rely on the app's "Ask Genie" panel, which passes the
  uploaded document text as additional context alongside the Genie space.

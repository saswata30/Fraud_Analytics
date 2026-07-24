import { useEffect, useState } from "react";
import { AlertTriangle, Banknote, ShieldAlert, TrendingUp } from "lucide-react";
import { api, Claim, Dashboard as DashData, fmtGbp, fmtNum, fmtPct } from "../lib/api";
import { BarChart, Donut, LineChart, RiskColumns } from "../components/charts";

export default function Dashboard() {
  const [d, setD] = useState<DashData | null>(null);
  const [claims, setClaims] = useState<Claim[]>([]);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    api.dashboard().then(setD).catch((e) => setErr(String(e)));
    api.highRisk(15).then(setClaims).catch(() => {});
  }, []);

  if (err) return <div className="page"><div className="loading">Couldn't load data.<br /><small>{err}</small></div></div>;
  if (!d) return <div className="page"><div className="loading">Loading fraud analytics…</div></div>;

  const k = d.kpi;
  const legit = k.total_claims - k.fraud_claims;

  return (
    <div className="page">
      <div className="sec-head">
        <div>
          <h2>Fraud Overview</h2>
          <p>Portfolio-wide claim fraud signals across regions, products and risk indicators.</p>
        </div>
      </div>

      {/* ---- KPI tiles ---- */}
      <div className="kpi-row">
        <KpiCard tone="red" icon={<ShieldAlert size={18} />} label="Fraud Rate"
          value={fmtPct(k.fraud_rate)} sub={`${fmtNum(k.fraud_claims)} of ${fmtNum(k.total_claims)} claims`} />
        <KpiCard tone="amber" icon={<Banknote size={18} />} label="Flagged Payout"
          value={fmtGbp(k.fraud_payout)} sub={`of ${fmtGbp(k.total_payout)} total`} />
        <KpiCard tone="blue" icon={<AlertTriangle size={18} />} label="High-Risk Claims"
          value={fmtNum(k.high_risk_claims)} sub="risk score ≥ 3" />
        <KpiCard tone="blue" icon={<TrendingUp size={18} />} label="Avg Claim"
          value={fmtGbp(k.avg_claim)} sub="all policies" />
      </div>

      {/* ---- Trend + split ---- */}
      <div className="grid-2">
        <div className="card">
          <div className="card-head">Fraud Rate Over Time</div>
          <div className="card-body">
            <LineChart
              points={d.trend.map((t) => ({ label: t.month, value: t.fraud_rate * 100 }))}
              color="#e2483b"
              yFmt={(v) => `${v.toFixed(0)}%`}
            />
          </div>
        </div>
        <div className="card">
          <div className="card-head">Fraud vs Legitimate</div>
          <div className="card-body donut-block">
            <Donut
              segments={[
                { label: "Fraud", value: k.fraud_claims, color: "#e2483b" },
                { label: "Legitimate", value: legit, color: "#c7d2e4" },
              ]}
            />
            <div className="donut-legend">
              <div className="dl-row"><i style={{ background: "#e2483b" }} /><span className="dl-name">Fraudulent</span><b>{fmtNum(k.fraud_claims)}</b></div>
              <div className="dl-row"><i style={{ background: "#c7d2e4" }} /><span className="dl-name">Legitimate</span><b>{fmtNum(legit)}</b></div>
              <div className="donut-center-label">{fmtPct(k.fraud_rate)}<span>fraud rate</span></div>
            </div>
          </div>
        </div>
      </div>

      {/* ---- Region / policy / risk ---- */}
      <div className="grid-3">
        <div className="card">
          <div className="card-head">Fraud Rate by Region</div>
          <div className="card-body">
            <BarChart rows={d.by_region.slice(0, 8).map((r) => ({ label: r.region, value: r.fraud_rate }))} />
          </div>
        </div>
        <div className="card">
          <div className="card-head">Fraud Rate by Policy Type</div>
          <div className="card-body">
            <BarChart rows={d.by_policy.map((r) => ({ label: r.policy_type, value: r.fraud_rate }))} />
          </div>
        </div>
        <div className="card">
          <div className="card-head">Risk Score Distribution</div>
          <div className="card-body">
            <RiskColumns buckets={d.risk_dist.map((b) => ({ score: b.score, fraud: b.fraud, legit: b.legit }))} />
            <div className="legend-sm">
              <span><i className="lg" style={{ background: "#e2483b" }} /> Fraud</span>
              <span><i className="lg" style={{ background: "#c7d2e4" }} /> Legitimate</span>
            </div>
          </div>
        </div>
      </div>

      {/* ---- High-risk claims table ---- */}
      <div className="card">
        <div className="card-head">Highest-Risk Claims</div>
        <table className="claims-tbl">
          <thead>
            <tr>
              <th>Claim</th><th>Policy</th><th>Type</th><th>Region</th><th>Channel</th>
              <th className="r">Amount</th><th className="c">Lag (d)</th><th className="c">Risk</th><th className="c">Fraud</th>
            </tr>
          </thead>
          <tbody>
            {claims.map((c) => (
              <tr key={c.claim_id}>
                <td className="mono">{c.claim_id}</td>
                <td>{c.policy_type}</td>
                <td className="muted">{c.claim_type}</td>
                <td>{c.region}</td>
                <td className="muted">{c.channel}</td>
                <td className="r b">{fmtGbp(c.claim_amount)}</td>
                <td className="c">{c.report_lag_days}</td>
                <td className="c"><span className={`riskpill r${c.fraud_risk_score}`}>{c.fraud_risk_score}</span></td>
                <td className="c">{c.is_fraud ? <span className="fraud-yes">Yes</span> : <span className="muted">No</span>}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function KpiCard({ tone, icon, label, value, sub }: {
  tone: string; icon: React.ReactNode; label: string; value: string; sub: string;
}) {
  return (
    <div className={`kpi ${tone}`}>
      <div className="kpi-ico">{icon}</div>
      <div className="kpi-meta">
        <span className="kpi-label">{label}</span>
        <b className="kpi-value">{value}</b>
        <span className="kpi-sub">{sub}</span>
      </div>
    </div>
  );
}

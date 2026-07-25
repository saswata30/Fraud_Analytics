import { useEffect, useState } from "react";
import { AlertTriangle, Banknote, Database, ExternalLink, ShieldAlert, TrendingUp, Layers } from "lucide-react";
import { api, Claim, Dashboard as DashData, Meta, fmtGbp, fmtNum, fmtPct } from "./lib/api";
import { LineArea, BarChart, RiskColumns, Donut } from "./components/charts";
import ChatPanel from "./components/ChatPanel";
import NewsPanel from "./components/NewsPanel";

export default function App() {
  const [meta, setMeta] = useState<Meta | null>(null);
  const [d, setD] = useState<DashData | null>(null);
  const [claims, setClaims] = useState<Claim[]>([]);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    api.meta().then(setMeta).catch(() => {});
    api.dashboard().then(setD).catch((e) => setErr(String(e)));
    api.highRisk(12).then(setClaims).catch(() => {});
  }, []);

  async function openUC() {
    try {
      const { url } = await api.ucLink("gold_fraud_claims");
      window.open(url, "_blank");
    } catch { /* ignore */ }
  }

  const k = d?.kpi;
  const legit = k ? k.total_claims - k.fraud_claims : 0;
  const lossRatio = k && k.total_payout ? k.fraud_payout / k.total_payout : 0;

  return (
    <div className="app">
      {/* ---------- top bar ---------- */}
      <header className="topbar">
        <div className="brand">
          <div className="brand-mark">A</div>
          <div className="brand-txt">
            <b>Allianz Fraud Intelligence</b>
            <span>Insurance claims · fraud detection · risk signals</span>
          </div>
        </div>
        <div className="top-right">
          <div className="event-pill"><Layers size={13} /> {meta ? `${meta.catalog}.${meta.schema}` : "fraud_analytics"}</div>
          <button className="uc-btn" onClick={openUC}><Database size={14} /> Unity Catalog <ExternalLink size={11} /></button>
        </div>
      </header>

      {err && <div className="app-err">Couldn't load fraud analytics — {err}</div>}

      {/* ---------- KPI row ---------- */}
      <div className="kpi-row">
        <Kpi tone="red" icon={<ShieldAlert size={17} />} label="Fraud Rate"
          value={k ? fmtPct(k.fraud_rate) : "—"} sub={k ? `${fmtNum(k.fraud_claims)} of ${fmtNum(k.total_claims)} claims` : ""} />
        <Kpi tone="amber" icon={<Banknote size={17} />} label="Flagged Payout"
          value={k ? fmtGbp(k.fraud_payout) : "—"} sub={k ? `of ${fmtGbp(k.total_payout)} total` : ""} />
        <Kpi tone="blue" icon={<AlertTriangle size={17} />} label="High-Risk Claims"
          value={k ? fmtNum(k.high_risk_claims) : "—"} sub="risk score ≥ 3" />
        <Kpi tone="violet" icon={<TrendingUp size={17} />} label="Fraud Loss Ratio"
          value={fmtPct(lossRatio)} sub="flagged ÷ total payout" />
        <Kpi tone="teal" icon={<Banknote size={17} />} label="Avg Claim"
          value={k ? fmtGbp(k.avg_claim) : "—"} sub="all policies" />
      </div>

      {/* ---------- main grid: content + docked chat ---------- */}
      <div className="layout">
        <div className="content">
          {/* trend + donut */}
          <div className="row row-2">
            <div className="card">
              <div className="card-head">
                <div className="ch-title">Fraud rate &amp; flagged payout over time</div>
                <div className="ch-sub">Monthly fraud rate (%) and fraudulent payout (£)</div>
              </div>
              <div className="card-body">
                {d ? (
                  <LineArea
                    data={d.trend.map((t) => ({ month: t.month, "Fraud rate %": +(t.fraud_rate * 100).toFixed(2), "Flagged payout £k": +(t.fraud_payout / 1000).toFixed(0) }))}
                    xKey="month"
                    series={[
                      { key: "Fraud rate %", label: "Fraud rate %", color: "#ff6b5e" },
                      { key: "Flagged payout £k", label: "Flagged payout £k", color: "#4f8bff" },
                    ]}
                    yFmt={(v) => v.toLocaleString()}
                  />
                ) : <div className="chart-empty">Loading…</div>}
              </div>
            </div>
            <div className="card">
              <div className="card-head"><div className="ch-title">Fraud vs legitimate</div><div className="ch-sub">Share of all claims</div></div>
              <div className="card-body donut-block">
                <Donut
                  segments={[
                    { label: "Fraudulent", value: k?.fraud_claims || 0, color: "#ff6b5e" },
                    { label: "Legitimate", value: legit, color: "#3b5578" },
                  ]}
                  centerTop={k ? fmtPct(k.fraud_rate) : "—"} centerSub="fraud rate"
                />
                <div className="donut-legend">
                  <div className="dl-row"><i style={{ background: "#ff6b5e" }} /><span>Fraudulent</span><b>{fmtNum(k?.fraud_claims || 0)}</b></div>
                  <div className="dl-row"><i style={{ background: "#3b5578" }} /><span>Legitimate</span><b>{fmtNum(legit)}</b></div>
                </div>
              </div>
            </div>
          </div>

          {/* region / policy / risk */}
          <div className="row row-3">
            <div className="card">
              <div className="card-head"><div className="ch-title">Fraud rate by region</div></div>
              <div className="card-body">
                {d ? <BarChart rows={d.by_region.slice(0, 8).map((r) => ({ label: r.region, value: r.fraud_rate }))}
                  colorFn={(_, v, max) => `rgba(255,107,94,${0.4 + 0.6 * (v / max)})`} /> : null}
              </div>
            </div>
            <div className="card">
              <div className="card-head"><div className="ch-title">Fraud rate by policy type</div></div>
              <div className="card-body">
                {d ? <BarChart rows={d.by_policy.map((r) => ({ label: r.policy_type, value: r.fraud_rate }))}
                  colorFn={(i) => ["#4f8bff", "#2dd4bf", "#a78bfa", "#f5b83d", "#ff6b5e", "#f0883e"][i % 6]} /> : null}
              </div>
            </div>
            <div className="card">
              <div className="card-head"><div className="ch-title">Risk-score distribution</div></div>
              <div className="card-body">
                {d ? <RiskColumns buckets={d.risk_dist.map((b) => ({ score: b.score, fraud: b.fraud, legit: b.legit }))} /> : null}
                <div className="legend-sm">
                  <span><i style={{ background: "#ff6b5e" }} /> Fraud</span>
                  <span><i style={{ background: "#3b5578" }} /> Legitimate</span>
                </div>
              </div>
            </div>
          </div>

          {/* news */}
          <NewsPanel />

          {/* high-risk table */}
          <div className="card">
            <div className="card-head"><div className="ch-title">Highest-risk claims to review</div></div>
            <div className="tbl-wrap">
              <table className="claims-tbl">
                <thead>
                  <tr>
                    <th>Claim</th><th>Policy</th><th>Region</th><th>Channel</th>
                    <th className="r">Amount</th><th className="c">Lag</th><th className="c">Risk</th><th className="c">Fraud</th>
                  </tr>
                </thead>
                <tbody>
                  {claims.map((c) => (
                    <tr key={c.claim_id}>
                      <td className="mono">{c.claim_id}</td>
                      <td>{c.policy_type}</td>
                      <td>{c.region}</td>
                      <td className="muted">{c.channel}</td>
                      <td className="r b">{fmtGbp(c.claim_amount)}</td>
                      <td className="c">{c.report_lag_days}d</td>
                      <td className="c"><span className={`riskpill r${c.fraud_risk_score}`}>{c.fraud_risk_score}</span></td>
                      <td className="c">{c.is_fraud ? <span className="fraud-yes">Yes</span> : <span className="muted">No</span>}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* docked chat */}
        <aside className="sidebar">
          <ChatPanel />
        </aside>
      </div>
    </div>
  );
}

function Kpi({ tone, icon, label, value, sub }: {
  tone: string; icon: React.ReactNode; label: string; value: string; sub: string;
}) {
  return (
    <div className={`kpi ${tone}`}>
      <div className="kpi-top">
        <span className="kpi-ico">{icon}</span>
        <span className="kpi-label">{label}</span>
      </div>
      <b className="kpi-value">{value}</b>
      <span className="kpi-sub">{sub}</span>
    </div>
  );
}

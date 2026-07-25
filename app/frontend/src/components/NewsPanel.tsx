import { useEffect, useState } from "react";
import { Newspaper, RefreshCw } from "lucide-react";
import { api, NewsItem } from "../lib/api";

const CAT_COLOR: Record<string, string> = {
  "Claims Fraud": "#ff6b5e",
  "Digital & Identity": "#4f8bff",
  "Organised Rings": "#a78bfa",
  "Regulation": "#f5b83d",
  "Detection Tech": "#2dd4bf",
  "Market Trend": "#8aa0bd",
};
const impactClass = (i: string) => (i === "High" ? "hi" : i === "Medium" ? "md" : "lo");

export default function NewsPanel() {
  const [items, setItems] = useState<NewsItem[] | null>(null);
  const [busy, setBusy] = useState(false);
  const [ai, setAi] = useState(true);

  function load(refresh = false) {
    setBusy(true);
    api.news(refresh)
      .then((r) => { setItems(r.items); setAi(r.source === "ai"); })
      .catch(() => setItems([]))
      .finally(() => setBusy(false));
  }
  useEffect(() => { load(false); }, []);

  return (
    <div className="card news-card">
      <div className="card-head news-head">
        <span className="news-title"><Newspaper size={15} /> Fraud in Insurance — News & Signals</span>
        <span className="news-badge">{ai ? "AI briefing" : "briefing"}</span>
        <button className="news-refresh" title="Regenerate briefing" disabled={busy} onClick={() => load(true)}>
          <RefreshCw size={13} className={busy ? "spin" : ""} />
        </button>
      </div>
      <div className="card-body news-body">
        {items === null && <div className="chart-empty">Loading briefing…</div>}
        {items && items.length === 0 && <div className="chart-empty">No briefing available.</div>}
        {items && items.map((it, i) => (
          <div className="news-item" key={i}>
            <div className="news-item-top">
              <span className="news-cat" style={{ color: CAT_COLOR[it.category] || "#8aa0bd", borderColor: (CAT_COLOR[it.category] || "#8aa0bd") + "55" }}>
                {it.category}
              </span>
              <span className={`news-impact ${impactClass(it.impact)}`}>{it.impact}</span>
            </div>
            <div className="news-headline">{it.headline}</div>
            <div className="news-summary">{it.summary}</div>
          </div>
        ))}
      </div>
      {items && !ai && (
        <div className="news-foot">Showing curated fallback items (AI endpoint unavailable).</div>
      )}
    </div>
  );
}
